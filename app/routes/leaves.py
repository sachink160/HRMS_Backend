from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from datetime import datetime
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
        # Validate dates
        if leave.start_date >= leave.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )
        
        if leave.start_date.date() < datetime.now().date():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot apply for leave in the past"
            )
        
        # Check for overlapping leaves
        existing_leave = await db.execute(
            select(Leave).where(
                Leave.user_id == current_user.id,
                Leave.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
                Leave.start_date <= leave.end_date,
                Leave.end_date >= leave.start_date
            )
        )
        if existing_leave.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have a leave application for this period"
            )
        
        # Create leave application
        db_leave = Leave(
            user_id=current_user.id,
            start_date=leave.start_date,
            end_date=leave.end_date,
            reason=leave.reason,
            status=LeaveStatus.PENDING
        )
        
        db.add(db_leave)
        await db.commit()
        await db.refresh(db_leave)
        
        log_info(f"Leave application created by user {current_user.email}")
        return db_leave
        
    except Exception as e:
        log_error(f"Leave application error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply for leave"
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
