from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime
from typing import List
from app.database import get_db
from app.models import User, Holiday
from app.schema import HolidayCreate, HolidayResponse, HolidayUpdate
from app.auth import get_current_user, get_current_admin_user
from app.logger import log_info, log_error

router = APIRouter(prefix="/holidays", tags=["holidays"])

@router.post("/", response_model=HolidayResponse)
async def create_holiday(
    holiday: HolidayCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new holiday (admin only)."""
    try:
        # Check if holiday already exists for this date
        existing_holiday = await db.execute(
            select(Holiday).where(Holiday.date == holiday.date)
        )
        if existing_holiday.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Holiday already exists for this date"
            )
        
        # Create holiday
        db_holiday = Holiday(
            date=holiday.date,
            title=holiday.title,
            description=holiday.description
        )
        
        db.add(db_holiday)
        await db.commit()
        await db.refresh(db_holiday)
        
        log_info(f"Holiday created by admin {current_user.email}: {holiday.title}")
        return db_holiday
        
    except Exception as e:
        log_error(f"Create holiday error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create holiday"
        )

@router.get("/", response_model=List[HolidayResponse])
async def get_holidays(
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all holidays."""
    try:
        result = await db.execute(
            select(Holiday)
            .offset(offset)
            .limit(limit)
            .order_by(Holiday.date.asc())
        )
        holidays = result.scalars().all()
        return holidays
        
    except Exception as e:
        log_error(f"Get holidays error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch holidays"
        )

@router.get("/upcoming", response_model=List[HolidayResponse])
async def get_upcoming_holidays(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get upcoming holidays."""
    try:
        today = datetime.now().date()
        result = await db.execute(
            select(Holiday)
            .where(Holiday.date >= today)
            .order_by(Holiday.date.asc())
        )
        holidays = result.scalars().all()
        return holidays
        
    except Exception as e:
        log_error(f"Get upcoming holidays error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch upcoming holidays"
        )

@router.get("/{holiday_id}", response_model=HolidayResponse)
async def get_holiday(
    holiday_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific holiday."""
    try:
        result = await db.execute(select(Holiday).where(Holiday.id == holiday_id))
        holiday = result.scalar_one_or_none()
        
        if not holiday:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Holiday not found"
            )
        
        return holiday
        
    except Exception as e:
        log_error(f"Get holiday error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch holiday"
        )

@router.put("/{holiday_id}", response_model=HolidayResponse)
async def update_holiday(
    holiday_id: int,
    holiday_update: HolidayUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update holiday (admin only)."""
    try:
        # Get holiday
        result = await db.execute(select(Holiday).where(Holiday.id == holiday_id))
        holiday = result.scalar_one_or_none()
        
        if not holiday:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Holiday not found"
            )
        
        # Update holiday fields
        update_data = holiday_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(holiday, field, value)
        
        await db.commit()
        await db.refresh(holiday)
        
        log_info(f"Holiday {holiday_id} updated by admin {current_user.email}")
        return holiday
        
    except Exception as e:
        log_error(f"Update holiday error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update holiday"
        )

@router.delete("/{holiday_id}")
async def delete_holiday(
    holiday_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete holiday (admin only)."""
    try:
        # Get holiday
        result = await db.execute(select(Holiday).where(Holiday.id == holiday_id))
        holiday = result.scalar_one_or_none()
        
        if not holiday:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Holiday not found"
            )
        
        # Delete holiday
        await db.execute(delete(Holiday).where(Holiday.id == holiday_id))
        await db.commit()
        
        log_info(f"Holiday {holiday_id} deleted by admin {current_user.email}")
        return {"message": "Holiday deleted successfully"}
        
    except Exception as e:
        log_error(f"Delete holiday error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete holiday"
        )
