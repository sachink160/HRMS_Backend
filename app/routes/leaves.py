from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from typing import List
from app.database import get_db
from app.models import User, Leave, LeaveStatus
from app.schema import LeaveCreate, LeaveResponse, LeaveUpdate, PaginationParams, PaginatedResponse
from app.auth import get_current_user, get_current_admin_user
from app.logger import log_info, log_error

router = APIRouter(prefix="/leaves", tags=["leaves"])

@router.post("/", response_model=LeaveResponse)
async def apply_leave(
    leave: LeaveCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Apply for leave."""
    try:
        log_info(f"Leave application attempt by user {current_user.email}: start_date={leave.start_date}, end_date={leave.end_date}")
        
        # Ensure dates are properly formatted datetime objects
        start_date = leave.start_date
        end_date = leave.end_date
        
        # If dates are naive, make them timezone-aware (UTC)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)  # Make timezone-aware
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)  # Make timezone-aware
        
        # Validate dates
        if start_date >= end_date:
            log_error(f"Invalid date range: start_date={start_date} >= end_date={end_date}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )
        
        if start_date.date() < datetime.now(timezone.utc).date():
            log_error(f"Past date application: start_date={start_date.date()} < today={datetime.now(timezone.utc).date()}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot apply for leave in the past"
            )
        
        # Calculate actual days between start and end date (inclusive)
        actual_days = (end_date.date() - start_date.date()).days + 1
        
        # Validate total_days doesn't exceed actual date range
        if leave.total_days > actual_days:
            log_error(f"Total days exceeds date range: total_days={leave.total_days} > actual_days={actual_days}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total days ({leave.total_days}) cannot be greater than the actual days in the selected period ({actual_days} days from {start_date.date()} to {end_date.date()})"
            )
        
        # Check for overlapping leaves
        existing_leave = await db.execute(
            select(Leave).where(
                Leave.user_id == current_user.id,
                Leave.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
                Leave.start_date <= end_date,
                Leave.end_date >= start_date
            )
        )
        if existing_leave.scalar_one_or_none():
            log_error(f"Overlapping leave found for user {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have a leave application for this period"
            )
        
        # Create leave application
        db_leave = Leave(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            total_days=leave.total_days,
            reason=leave.reason,
            status=LeaveStatus.PENDING
        )
        
        db.add(db_leave)
        await db.commit()
        await db.refresh(db_leave)
        
        log_info(f"Leave application created successfully by user {current_user.email}, leave_id={db_leave.id}")
        return db_leave
        
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        log_error(f"Leave application error for user {current_user.email}: {str(e)}")
        log_error(f"Leave data: start_date={leave.start_date}, end_date={leave.end_date}, reason={leave.reason}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply for leave: {str(e)}"
        )

@router.get("/my-leaves", response_model=List[LeaveResponse])
async def get_my_leaves(
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's leave applications."""
    try:
        from app.database import monitor_query
        
        async with monitor_query("get_my_leaves"):
            result = await db.execute(
                select(Leave)
                .where(Leave.user_id == current_user.id)
                .offset(offset)
                .limit(limit)
                .order_by(Leave.created_at.desc())
            )
            leaves = result.scalars().all()
            return leaves
        
    except Exception as e:
        log_error(f"Get my leaves error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch leaves"
        )

@router.get("/", response_model=List[LeaveResponse])
async def get_all_leaves(
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all leave applications (admin only)."""
    try:
        result = await db.execute(
            select(Leave)
            .options(selectinload(Leave.user))
            .offset(offset)
            .limit(limit)
            .order_by(Leave.created_at.desc())
        )
        leaves = result.scalars().all()
        return leaves
        
    except Exception as e:
        log_error(f"Get all leaves error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch leaves"
        )

@router.put("/{leave_id}", response_model=LeaveResponse)
async def update_leave(
    leave_id: int,
    leave_update: LeaveUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update leave application. Users can only edit pending leaves, admins can edit any."""
    try:
        # Get leave application
        result = await db.execute(select(Leave).where(Leave.id == leave_id))
        leave = result.scalar_one_or_none()
        
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave application not found"
            )
        
        # Permission checks
        is_admin = current_user.role in ["admin", "super_admin"]
        is_owner = leave.user_id == current_user.id
        
        if not is_admin and not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to edit this leave"
            )
        
        # Regular users can only edit pending leaves
        if not is_admin and leave.status != LeaveStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You can only edit pending leave applications"
            )
        
        # Update fields if provided
        if leave_update.start_date is not None:
            start_date = leave_update.start_date
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            leave.start_date = start_date
            
        if leave_update.end_date is not None:
            end_date = leave_update.end_date
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            leave.end_date = end_date
            
        if leave_update.total_days is not None:
            leave.total_days = leave_update.total_days
            
        if leave_update.reason is not None:
            leave.reason = leave_update.reason
            
        # Only admins can update status
        if leave_update.status is not None and is_admin:
            leave.status = leave_update.status
        
        # Validate dates if both are provided
        if leave_update.start_date is not None or leave_update.end_date is not None:
            if leave.start_date >= leave.end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start date must be before end date"
                )
            
            if leave.start_date.date() < datetime.now(timezone.utc).date():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot apply for leave in the past"
                )
            
            # Calculate actual days between start and end date (inclusive)
            actual_days = (leave.end_date.date() - leave.start_date.date()).days + 1
            
            # Validate total_days doesn't exceed actual date range
            if leave.total_days > actual_days:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Total days ({leave.total_days}) cannot be greater than the actual days in the selected period ({actual_days} days from {leave.start_date.date()} to {leave.end_date.date()})"
                )
        
        await db.commit()
        await db.refresh(leave)
        
        log_info(f"Leave {leave_id} updated by user {current_user.email}")
        return leave
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Update leave error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update leave application"
        )

@router.put("/{leave_id}/status", response_model=LeaveResponse)
async def update_leave_status(
    leave_id: int,
    leave_update: LeaveUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update leave status (admin only)."""
    try:
        # Get leave application
        result = await db.execute(select(Leave).where(Leave.id == leave_id))
        leave = result.scalar_one_or_none()
        
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave application not found"
            )
        
        # Update status
        leave.status = leave_update.status
        await db.commit()
        await db.refresh(leave)
        
        log_info(f"Leave {leave_id} status updated to {leave_update.status} by admin {current_user.email}")
        return leave
        
    except Exception as e:
        log_error(f"Update leave status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update leave status"
        )

@router.get("/{leave_id}", response_model=LeaveResponse)
async def get_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific leave application."""
    try:
        result = await db.execute(
            select(Leave)
            .options(selectinload(Leave.user))
            .where(Leave.id == leave_id)
        )
        leave = result.scalar_one_or_none()
        
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave application not found"
            )
        
        # Check if user can access this leave
        if current_user.role != "admin" and leave.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        return leave
        
    except Exception as e:
        log_error(f"Get leave error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch leave"
        )
