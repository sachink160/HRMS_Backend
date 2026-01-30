from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from datetime import datetime, date
from typing import List, Optional
from app.database import get_db
from app.models import User, Holiday
from app.schema import HolidayCreate, HolidayResponse, HolidayUpdate
from app.auth import get_current_user, get_current_admin_user
from app.logger import log_info, log_error
from app.response import APIResponse

router = APIRouter(prefix="/holidays", tags=["holidays"])

def holiday_to_dict(holiday: Holiday) -> dict:
    """Convert Holiday model to dictionary for response."""
    return {
        "id": holiday.id,
        "date": holiday.date.isoformat() if holiday.date else None,
        "title": holiday.title,
        "description": holiday.description,
        "is_active": holiday.is_active,
        "created_at": holiday.created_at.isoformat() if holiday.created_at else None,
        "updated_at": holiday.updated_at.isoformat() if holiday.updated_at else None,
    }

@router.post("/")
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
            return APIResponse.bad_request(message="Holiday already exists for this date")
        
        # Create holiday
        db_holiday = Holiday(
            date=holiday.date,
            title=holiday.title,
            description=holiday.description,
            is_active=holiday.is_active if hasattr(holiday, 'is_active') and holiday.is_active is not None else True
        )
        
        db.add(db_holiday)
        await db.commit()
        await db.refresh(db_holiday)
        
        log_info(f"Holiday created by admin {current_user.email}: {holiday.title}")
        return APIResponse.created(
            data=holiday_to_dict(db_holiday),
            message="Holiday created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Create holiday error: {str(e)}")
        return APIResponse.internal_error(message="Failed to create holiday")

@router.get("/")
async def get_holidays(
    offset: int = 0,
    limit: int = 10,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all holidays with optional date range filter."""
    try:
        query = select(Holiday)
        
        if start_date:
            query = query.where(Holiday.date >= start_date)
        if end_date:
            query = query.where(Holiday.date <= end_date)
            
        result = await db.execute(
            query
            .offset(offset)
            .limit(limit)
            .order_by(Holiday.date.asc())
        )
        holidays = result.scalars().all()
        holidays_data = [holiday_to_dict(h) for h in holidays]
        return APIResponse.success(
            data=holidays_data,
            message="Holidays retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get holidays error: {str(e)}")
        return APIResponse.internal_error(message="Failed to fetch holidays")

@router.get("/upcoming")
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
        holidays_data = [holiday_to_dict(h) for h in holidays]
        return APIResponse.success(
            data=holidays_data,
            message="Upcoming holidays retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get upcoming holidays error: {str(e)}")
        return APIResponse.internal_error(message="Failed to fetch upcoming holidays")

@router.get("/{holiday_id}")
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
            return APIResponse.not_found(message="Holiday not found", resource="holiday")
        
        return APIResponse.success(
            data=holiday_to_dict(holiday),
            message="Holiday retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get holiday error: {str(e)}")
        return APIResponse.internal_error(message="Failed to fetch holiday")

@router.put("/{holiday_id}")
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
            return APIResponse.not_found(message="Holiday not found", resource="holiday")
        
        # Update holiday fields
        update_data = holiday_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(holiday, field, value)
        
        await db.commit()
        await db.refresh(holiday)
        
        log_info(f"Holiday {holiday_id} updated by admin {current_user.email}")
        return APIResponse.success(
            data=holiday_to_dict(holiday),
            message="Holiday updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Update holiday error: {str(e)}")
        return APIResponse.internal_error(message="Failed to update holiday")

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
            return APIResponse.not_found(message="Holiday not found", resource="holiday")
        
        # Delete holiday
        await db.execute(delete(Holiday).where(Holiday.id == holiday_id))
        await db.commit()
        
        log_info(f"Holiday {holiday_id} deleted by admin {current_user.email}")
        return APIResponse.success(
            data={},
            message="Holiday deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Delete holiday error: {str(e)}")
        return APIResponse.internal_error(message="Failed to delete holiday")
