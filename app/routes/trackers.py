from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import selectinload
from datetime import datetime, date
from typing import List, Optional
from app.database import get_db
from app.models import User, UserTracker
from app.schema import TrackerResponse
from app.auth import get_current_user, get_current_admin_user
from app.logger import log_info, log_error

router = APIRouter(prefix="/trackers", tags=["trackers"])

@router.post("/check-in", response_model=TrackerResponse)
async def check_in(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check in for the day."""
    try:
        today = datetime.now().date()
        current_time = datetime.now()
        
        # Check if already checked in today
        existing_tracker = await db.execute(
            select(UserTracker).where(
                and_(
                    UserTracker.user_id == current_user.id,
                    func.date(UserTracker.date) == today,
                    UserTracker.check_in.isnot(None)
                )
            )
        )
        if existing_tracker.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked in today"
            )
        
        # Check if user is trying to check in on a future date
        if today > datetime.now().date():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot check in for future dates"
            )
        
        # Create or update tracker record
        tracker = await db.execute(
            select(UserTracker).where(
                and_(
                    UserTracker.user_id == current_user.id,
                    func.date(UserTracker.date) == today
                )
            )
        )
        tracker_record = tracker.scalar_one_or_none()
        
        if tracker_record:
            tracker_record.check_in = current_time
        else:
            tracker_record = UserTracker(
                user_id=current_user.id,
                check_in=current_time,
                date=today
            )
            db.add(tracker_record)
        
        await db.commit()
        await db.refresh(tracker_record)
        
        log_info(f"User {current_user.email} checked in at {current_time}")
        return tracker_record
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Check-in error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check in"
        )

@router.post("/check-out", response_model=TrackerResponse)
async def check_out(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check out for the day."""
    try:
        today = datetime.now().date()
        current_time = datetime.now()
        
        # Check if already checked in today
        existing_tracker = await db.execute(
            select(UserTracker).where(
                and_(
                    UserTracker.user_id == current_user.id,
                    func.date(UserTracker.date) == today,
                    UserTracker.check_in.isnot(None)
                )
            )
        )
        tracker_record = existing_tracker.scalar_one_or_none()
        
        if not tracker_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must check in before checking out"
            )
        
        if tracker_record.check_out is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked out today"
            )
        
        # Check if check-out time is before check-in time
        if current_time <= tracker_record.check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Check-out time must be after check-in time"
            )
        
        # Update check out time
        tracker_record.check_out = current_time
        await db.commit()
        await db.refresh(tracker_record)
        
        log_info(f"User {current_user.email} checked out at {current_time}")
        return tracker_record
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Check-out error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check out"
        )

@router.get("/my-tracking", response_model=List[TrackerResponse])
async def get_my_tracking(
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's tracking records."""
    try:
        result = await db.execute(
            select(UserTracker)
            .where(UserTracker.user_id == current_user.id)
            .offset(offset)
            .limit(limit)
            .order_by(UserTracker.date.desc())
        )
        trackers = result.scalars().all()
        return trackers
        
    except Exception as e:
        log_error(f"Get my tracking error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tracking records"
        )

@router.get("/today", response_model=Optional[TrackerResponse])
async def get_today_tracking(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get today's tracking record for current user."""
    try:
        today = datetime.now().date()
        result = await db.execute(
            select(UserTracker).where(
                and_(
                    UserTracker.user_id == current_user.id,
                    func.date(UserTracker.date) == today
                )
            )
        )
        tracker = result.scalar_one_or_none()
        return tracker
        
    except Exception as e:
        log_error(f"Get today tracking error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch today's tracking record"
        )

@router.get("/today-status")
async def get_today_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get today's status with calculated total hours."""
    try:
        today = datetime.now().date()
        result = await db.execute(
            select(UserTracker).where(
                and_(
                    UserTracker.user_id == current_user.id,
                    func.date(UserTracker.date) == today
                )
            )
        )
        tracker = result.scalar_one_or_none()
        
        if not tracker:
            return {
                "check_in_time": None,
                "check_out_time": None,
                "total_hours": None
            }
        
        # Calculate total hours if both check-in and check-out exist
        total_hours = None
        if tracker.check_in and tracker.check_out:
            time_diff = tracker.check_out - tracker.check_in
            total_hours = round(time_diff.total_seconds() / 3600, 2)
        
        return {
            "check_in_time": tracker.check_in.isoformat() if tracker.check_in else None,
            "check_out_time": tracker.check_out.isoformat() if tracker.check_out else None,
            "total_hours": total_hours
        }
        
    except Exception as e:
        log_error(f"Get today status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch today's status"
        )

@router.get("/my-attendance", response_model=List[TrackerResponse])
async def get_my_attendance(
    offset: int = 0,
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's attendance history."""
    try:
        result = await db.execute(
            select(UserTracker)
            .where(UserTracker.user_id == current_user.id)
            .offset(offset)
            .limit(limit)
            .order_by(UserTracker.date.desc())
        )
        trackers = result.scalars().all()
        
        # Add calculated total hours to each record
        for tracker in trackers:
            if tracker.check_in and tracker.check_out:
                time_diff = tracker.check_out - tracker.check_in
                tracker.total_hours = round(time_diff.total_seconds() / 3600, 2)
            else:
                tracker.total_hours = None
        
        return trackers
        
    except Exception as e:
        log_error(f"Get my attendance error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch attendance records"
        )

@router.get("/", response_model=List[TrackerResponse])
async def get_all_tracking(
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all tracking records (admin only)."""
    try:
        result = await db.execute(
            select(UserTracker)
            .options(selectinload(UserTracker.user))
            .offset(offset)
            .limit(limit)
            .order_by(UserTracker.date.desc())
        )
        trackers = result.scalars().all()
        return trackers
        
    except Exception as e:
        log_error(f"Get all tracking error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tracking records"
        )

@router.get("/user/{user_id}", response_model=List[TrackerResponse])
async def get_user_tracking(
    user_id: int,
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tracking records for specific user (admin only)."""
    try:
        result = await db.execute(
            select(UserTracker)
            .where(UserTracker.user_id == user_id)
            .offset(offset)
            .limit(limit)
            .order_by(UserTracker.date.desc())
        )
        trackers = result.scalars().all()
        return trackers
        
    except Exception as e:
        log_error(f"Get user tracking error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user tracking records"
        )
