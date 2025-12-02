from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, distinct
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, date, timezone, timedelta
import json

from app.database import get_db
from app.auth import get_current_user, get_current_admin_user
from app.models import User, TimeLog, TimeLogStatus, UserRole
from app.schema import (
    TimeLogCreate, TimeLogResponse, TimeLogSummary, TimeLogStatistics,
    EmployeeTimeLogResponse, BreakInfo, PaginatedResponse
)
from app.logger import log_info, log_error

router = APIRouter(prefix="/time-tracker", tags=["time-tracker"])

# Helper functions
def parse_breaks(breaks_json: Optional[str]) -> List[BreakInfo]:
    """Parse breaks JSON string to list of BreakInfo."""
    if not breaks_json:
        return []
    try:
        breaks_data = json.loads(breaks_json)
        breaks = []
        for break_data in breaks_data:
            break_info = BreakInfo(
                start=datetime.fromisoformat(break_data['start']) if isinstance(break_data['start'], str) else break_data['start'],
                end=datetime.fromisoformat(break_data['end']) if break_data.get('end') and isinstance(break_data['end'], str) else break_data.get('end'),
                duration=break_data.get('duration')
            )
            breaks.append(break_info)
        return breaks
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        log_error(f"Error parsing breaks JSON: {str(e)}")
        return []

def serialize_breaks(breaks: List[BreakInfo]) -> str:
    """Serialize breaks list to JSON string."""
    if not breaks:
        return None
    breaks_data = []
    for break_info in breaks:
        break_dict = {
            'start': break_info.start.isoformat() if isinstance(break_info.start, datetime) else str(break_info.start),
            'end': break_info.end.isoformat() if break_info.end and isinstance(break_info.end, datetime) else (str(break_info.end) if break_info.end else None),
            'duration': break_info.duration
        }
        breaks_data.append(break_dict)
    return json.dumps(breaks_data)

def calculate_break_duration(breaks: List[BreakInfo]) -> int:
    """Calculate total break duration in seconds."""
    total = 0
    for break_info in breaks:
        if break_info.end and break_info.start:
            duration = (break_info.end - break_info.start).total_seconds()
            total += int(duration)
        elif break_info.duration:
            total += break_info.duration
    return total

def calculate_work_duration(start_time: datetime, end_time: Optional[datetime], break_duration: int) -> Optional[int]:
    """Calculate total work duration in seconds (excluding breaks)."""
    if not end_time:
        return None
    total_duration = (end_time - start_time).total_seconds()
    return int(total_duration) - break_duration

# Employee Routes
@router.post("/start", response_model=TimeLogResponse)
async def start_timer(
    time_log: Optional[TimeLogCreate] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start the timer for the current user."""
    try:
        now = datetime.now(timezone.utc)
        today = now.date()
        
        # Check if there's already an active time log for today
        existing_query = select(TimeLog).where(
            and_(
                TimeLog.user_id == current_user.id,
                TimeLog.log_date == today,
                TimeLog.status.in_([TimeLogStatus.ACTIVE, TimeLogStatus.ON_BREAK])
            )
        )
        result = await db.execute(existing_query)
        existing_log = result.scalar_one_or_none()
        
        if existing_log:
            raise HTTPException(
                status_code=400,
                detail="Timer is already running for today. Please stop it first or take a break."
            )
        
        # Create new time log
        db_time_log = TimeLog(
            user_id=current_user.id,
            log_date=today,
            start_time=now,
            status=TimeLogStatus.ACTIVE,
            total_break_duration=0,
            notes=time_log.notes if time_log else None
        )
        
        db.add(db_time_log)
        await db.commit()
        await db.refresh(db_time_log)
        await db.refresh(db_time_log, ['user'])
        
        log_info(f"Timer started for user {current_user.email} on {today}")
        
        # Parse breaks for response
        breaks = parse_breaks(db_time_log.breaks)
        response = TimeLogResponse(
            id=db_time_log.id,
            user_id=db_time_log.user_id,
            log_date=db_time_log.log_date,
            start_time=db_time_log.start_time,
            end_time=db_time_log.end_time,
            breaks=breaks if breaks else None,
            total_break_duration=db_time_log.total_break_duration,
            total_work_duration=db_time_log.total_work_duration,
            status=db_time_log.status,
            notes=db_time_log.notes,
            created_at=db_time_log.created_at,
            updated_at=db_time_log.updated_at,
            user=db_time_log.user
        )
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        log_error(f"Error starting timer: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start timer")

@router.post("/stop", response_model=TimeLogResponse)
async def stop_timer(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stop the timer for the current user."""
    try:
        today = date.today()
        
        # Find active time log for today
        query = select(TimeLog).where(
            and_(
                TimeLog.user_id == current_user.id,
                TimeLog.log_date == today,
                TimeLog.status.in_([TimeLogStatus.ACTIVE, TimeLogStatus.ON_BREAK])
            )
        )
        result = await db.execute(query)
        time_log = result.scalar_one_or_none()
        
        if not time_log:
            raise HTTPException(
                status_code=404,
                detail="No active timer found for today. Please start the timer first."
            )
        
        now = datetime.now(timezone.utc)
        
        # If on break, end the break first
        if time_log.status == TimeLogStatus.ON_BREAK:
            breaks = parse_breaks(time_log.breaks)
            if breaks and breaks[-1].end is None:
                breaks[-1].end = now
                breaks[-1].duration = int((now - breaks[-1].start).total_seconds())
                time_log.breaks = serialize_breaks(breaks)
                time_log.total_break_duration = calculate_break_duration(breaks)
        
        # Update time log
        time_log.end_time = now
        time_log.status = TimeLogStatus.COMPLETED
        time_log.total_work_duration = calculate_work_duration(
            time_log.start_time,
            now,
            time_log.total_break_duration
        )
        
        await db.commit()
        await db.refresh(time_log, ['user'])
        
        log_info(f"Timer stopped for user {current_user.email} on {today}")
        
        # Parse breaks for response
        breaks = parse_breaks(time_log.breaks)
        response = TimeLogResponse(
            id=time_log.id,
            user_id=time_log.user_id,
            log_date=time_log.log_date,
            start_time=time_log.start_time,
            end_time=time_log.end_time,
            breaks=breaks if breaks else None,
            total_break_duration=time_log.total_break_duration,
            total_work_duration=time_log.total_work_duration,
            status=time_log.status,
            notes=time_log.notes,
            created_at=time_log.created_at,
            updated_at=time_log.updated_at,
            user=time_log.user
        )
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        log_error(f"Error stopping timer: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop timer")

@router.post("/break/start", response_model=TimeLogResponse)
async def start_break(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a break for the current user."""
    try:
        today = date.today()
        
        # Find active time log for today
        query = select(TimeLog).where(
            and_(
                TimeLog.user_id == current_user.id,
                TimeLog.log_date == today,
                TimeLog.status == TimeLogStatus.ACTIVE
            )
        )
        result = await db.execute(query)
        time_log = result.scalar_one_or_none()
        
        if not time_log:
            raise HTTPException(
                status_code=404,
                detail="No active timer found. Please start the timer first."
            )
        
        # Check if already on break
        if time_log.status == TimeLogStatus.ON_BREAK:
            breaks = parse_breaks(time_log.breaks)
            if breaks and breaks[-1].end is None:
                raise HTTPException(
                    status_code=400,
                    detail="Break is already in progress. Please end the break first."
                )
        
        # Add new break
        now = datetime.now(timezone.utc)
        breaks = parse_breaks(time_log.breaks)
        new_break = BreakInfo(start=now)
        breaks.append(new_break)
        
        time_log.breaks = serialize_breaks(breaks)
        time_log.status = TimeLogStatus.ON_BREAK
        
        await db.commit()
        await db.refresh(time_log, ['user'])
        
        log_info(f"Break started for user {current_user.email} on {today}")
        
        # Parse breaks for response
        breaks_parsed = parse_breaks(time_log.breaks)
        response = TimeLogResponse(
            id=time_log.id,
            user_id=time_log.user_id,
            log_date=time_log.log_date,
            start_time=time_log.start_time,
            end_time=time_log.end_time,
            breaks=breaks_parsed if breaks_parsed else None,
            total_break_duration=time_log.total_break_duration,
            total_work_duration=time_log.total_work_duration,
            status=time_log.status,
            notes=time_log.notes,
            created_at=time_log.created_at,
            updated_at=time_log.updated_at,
            user=time_log.user
        )
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        log_error(f"Error starting break: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start break")

@router.post("/break/end", response_model=TimeLogResponse)
async def end_break(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """End the current break for the current user."""
    try:
        today = date.today()
        
        # Find time log on break for today
        query = select(TimeLog).where(
            and_(
                TimeLog.user_id == current_user.id,
                TimeLog.log_date == today,
                TimeLog.status == TimeLogStatus.ON_BREAK
            )
        )
        result = await db.execute(query)
        time_log = result.scalar_one_or_none()
        
        if not time_log:
            raise HTTPException(
                status_code=404,
                detail="No active break found. Please start a break first."
            )
        
        # End the current break
        now = datetime.now(timezone.utc)
        breaks = parse_breaks(time_log.breaks)
        
        if not breaks or breaks[-1].end is not None:
            raise HTTPException(
                status_code=400,
                detail="No active break to end."
            )
        
        breaks[-1].end = now
        breaks[-1].duration = int((now - breaks[-1].start).total_seconds())
        
        # Update break duration
        time_log.breaks = serialize_breaks(breaks)
        time_log.total_break_duration = calculate_break_duration(breaks)
        time_log.status = TimeLogStatus.ACTIVE
        
        await db.commit()
        await db.refresh(time_log, ['user'])
        
        log_info(f"Break ended for user {current_user.email} on {today}")
        
        # Parse breaks for response
        breaks_parsed = parse_breaks(time_log.breaks)
        response = TimeLogResponse(
            id=time_log.id,
            user_id=time_log.user_id,
            log_date=time_log.log_date,
            start_time=time_log.start_time,
            end_time=time_log.end_time,
            breaks=breaks_parsed if breaks_parsed else None,
            total_break_duration=time_log.total_break_duration,
            total_work_duration=time_log.total_work_duration,
            status=time_log.status,
            notes=time_log.notes,
            created_at=time_log.created_at,
            updated_at=time_log.updated_at,
            user=time_log.user
        )
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        log_error(f"Error ending break: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end break")

@router.get("/current", response_model=TimeLogResponse)
async def get_current_timer(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the current active timer for the current user."""
    try:
        today = date.today()
        
        query = select(TimeLog).where(
            and_(
                TimeLog.user_id == current_user.id,
                TimeLog.log_date == today,
                TimeLog.status.in_([TimeLogStatus.ACTIVE, TimeLogStatus.ON_BREAK])
            )
        ).options(selectinload(TimeLog.user))
        
        result = await db.execute(query)
        time_log = result.scalar_one_or_none()
        
        if not time_log:
            raise HTTPException(
                status_code=404,
                detail="No active timer found for today."
            )
        
        # Parse breaks for response
        breaks = parse_breaks(time_log.breaks)
        response = TimeLogResponse(
            id=time_log.id,
            user_id=time_log.user_id,
            log_date=time_log.log_date,
            start_time=time_log.start_time,
            end_time=time_log.end_time,
            breaks=breaks if breaks else None,
            total_break_duration=time_log.total_break_duration,
            total_work_duration=time_log.total_work_duration,
            status=time_log.status,
            notes=time_log.notes,
            created_at=time_log.created_at,
            updated_at=time_log.updated_at,
            user=time_log.user
        )
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error retrieving current timer: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve current timer")

@router.get("/logs", response_model=List[TimeLogSummary])
async def get_my_time_logs(
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    limit: int = Query(30, ge=1, le=100, description="Number of days to retrieve"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get time logs for the current user."""
    try:
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=limit-1)
        
        query = select(TimeLog).where(
            and_(
                TimeLog.user_id == current_user.id,
                TimeLog.log_date >= start_date,
                TimeLog.log_date <= end_date
            )
        ).order_by(TimeLog.log_date.desc())
        
        result = await db.execute(query)
        time_logs = result.scalars().all()
        
        # Convert to summary format
        summaries = []
        for log in time_logs:
            total_work_hours = log.total_work_duration / 3600.0 if log.total_work_duration else None
            total_break_hours = log.total_break_duration / 3600.0 if log.total_break_duration else None
            
            # Calculate total hours (start to end)
            total_hours = None
            if log.start_time and log.end_time:
                total_seconds = (log.end_time - log.start_time).total_seconds()
                total_hours = total_seconds / 3600.0
            
            breaks = parse_breaks(log.breaks)
            
            summary = TimeLogSummary(
                log_date=log.log_date,
                start_time=log.start_time,
                end_time=log.end_time,
                total_work_hours=total_work_hours,
                total_break_hours=total_break_hours,
                total_hours=total_hours,
                breaks_count=len(breaks) if breaks else 0,
                status=log.status,
                time_log_id=log.id
            )
            summaries.append(summary)
        
        log_info(f"Retrieved {len(summaries)} time logs for user {current_user.email}")
        return summaries
        
    except Exception as e:
        log_error(f"Error retrieving time logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve time logs")

@router.get("/statistics", response_model=TimeLogStatistics)
async def get_my_statistics(
    start_date: Optional[date] = Query(None, description="Start date for statistics"),
    end_date: Optional[date] = Query(None, description="End date for statistics"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get time tracking statistics for the current user."""
    try:
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get all time logs in the period
        query = select(TimeLog).where(
            and_(
                TimeLog.user_id == current_user.id,
                TimeLog.log_date >= start_date,
                TimeLog.log_date <= end_date,
                TimeLog.status == TimeLogStatus.COMPLETED
            )
        )
        result = await db.execute(query)
        time_logs = result.scalars().all()
        
        # Calculate statistics
        total_work_seconds = sum(log.total_work_duration or 0 for log in time_logs)
        total_break_seconds = sum(log.total_break_duration or 0 for log in time_logs)
        total_work_hours = total_work_seconds / 3600.0
        total_break_hours = total_break_seconds / 3600.0
        
        days_with_logs = len(set(log.log_date for log in time_logs))
        total_days = (end_date - start_date).days + 1
        
        average_hours_per_day = total_work_hours / days_with_logs if days_with_logs > 0 else None
        average_break_hours_per_day = total_break_hours / days_with_logs if days_with_logs > 0 else None
        
        # Get current status
        today = date.today()
        current_query = select(TimeLog).where(
            and_(
                TimeLog.user_id == current_user.id,
                TimeLog.log_date == today,
                TimeLog.status.in_([TimeLogStatus.ACTIVE, TimeLogStatus.ON_BREAK])
            )
        )
        current_result = await db.execute(current_query)
        current_log = current_result.scalar_one_or_none()
        current_status = current_log.status if current_log else None
        
        # Get today's hours
        today_query = select(TimeLog).where(
            and_(
                TimeLog.user_id == current_user.id,
                TimeLog.log_date == today
            )
        )
        today_result = await db.execute(today_query)
        today_log = today_result.scalar_one_or_none()
        
        today_work_hours = None
        today_break_hours = None
        if today_log:
            if today_log.total_work_duration:
                today_work_hours = today_log.total_work_duration / 3600.0
            if today_log.total_break_duration:
                today_break_hours = today_log.total_break_duration / 3600.0
        
        statistics = TimeLogStatistics(
            total_work_hours=total_work_hours,
            total_break_hours=total_break_hours,
            total_days=total_days,
            average_hours_per_day=average_hours_per_day,
            average_break_hours_per_day=average_break_hours_per_day,
            days_with_logs=days_with_logs,
            current_status=current_status,
            today_work_hours=today_work_hours,
            today_break_hours=today_break_hours
        )
        
        log_info(f"Statistics retrieved for user {current_user.email}")
        return statistics
        
    except Exception as e:
        log_error(f"Error retrieving statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

# Admin Routes
@router.get("/admin/logs", response_model=PaginatedResponse)
async def get_all_time_logs_admin(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    status: Optional[TimeLogStatus] = Query(None, description="Filter by status"),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all time logs across all users (Admin only)."""
    try:
        # Build query
        query = select(TimeLog).options(selectinload(TimeLog.user))
        
        # Apply filters
        if user_id:
            query = query.where(TimeLog.user_id == user_id)
        
        if start_date:
            query = query.where(TimeLog.log_date >= start_date)
        
        if end_date:
            query = query.where(TimeLog.log_date <= end_date)
        
        if status:
            query = query.where(TimeLog.status == status)
        
        # Get total count
        count_query = select(func.count(TimeLog.id))
        if user_id:
            count_query = count_query.where(TimeLog.user_id == user_id)
        if start_date:
            count_query = count_query.where(TimeLog.log_date >= start_date)
        if end_date:
            count_query = count_query.where(TimeLog.log_date <= end_date)
        if status:
            count_query = count_query.where(TimeLog.status == status)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(TimeLog.log_date.desc(), TimeLog.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        time_logs = result.scalars().all()
        
        # Convert to response format
        log_dicts = []
        for log in time_logs:
            breaks = parse_breaks(log.breaks)
            total_work_hours = log.total_work_duration / 3600.0 if log.total_work_duration else None
            total_break_hours = log.total_break_duration / 3600.0 if log.total_break_duration else None
            
            log_dict = {
                "id": log.id,
                "user_id": log.user_id,
                "user_name": log.user.name if log.user else None,
                "user_email": log.user.email if log.user else None,
                "employee_id": log.user.employee_id if log.user else None,
                "log_date": log.log_date.isoformat(),
                "start_time": log.start_time.isoformat() if log.start_time else None,
                "end_time": log.end_time.isoformat() if log.end_time else None,
                "breaks": [{
                    "start": b.start.isoformat(),
                    "end": b.end.isoformat() if b.end else None,
                    "duration": b.duration
                } for b in breaks] if breaks else None,
                "total_break_duration": log.total_break_duration,
                "total_work_duration": log.total_work_duration,
                "total_work_hours": total_work_hours,
                "total_break_hours": total_break_hours,
                "status": log.status.value,
                "notes": log.notes,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "updated_at": log.updated_at.isoformat() if log.updated_at else None
            }
            log_dicts.append(log_dict)
        
        log_info(f"Admin {current_user.email} retrieved {len(log_dicts)} time logs")
        return PaginatedResponse(
            items=log_dicts,
            total=total,
            offset=offset,
            limit=limit
        )
        
    except Exception as e:
        log_error(f"Error retrieving all time logs for admin: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve time logs")

@router.get("/admin/statistics", response_model=TimeLogStatistics)
async def get_admin_statistics(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[date] = Query(None, description="Start date for statistics"),
    end_date: Optional[date] = Query(None, description="End date for statistics"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get time tracking statistics (Admin only)."""
    try:
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Build query
        query = select(TimeLog).where(
            and_(
                TimeLog.log_date >= start_date,
                TimeLog.log_date <= end_date,
                TimeLog.status == TimeLogStatus.COMPLETED
            )
        )
        
        if user_id:
            query = query.where(TimeLog.user_id == user_id)
        
        result = await db.execute(query)
        time_logs = result.scalars().all()
        
        # Calculate statistics
        total_work_seconds = sum(log.total_work_duration or 0 for log in time_logs)
        total_break_seconds = sum(log.total_break_duration or 0 for log in time_logs)
        total_work_hours = total_work_seconds / 3600.0
        total_break_hours = total_break_seconds / 3600.0
        
        days_with_logs = len(set(log.log_date for log in time_logs))
        total_days = (end_date - start_date).days + 1
        
        average_hours_per_day = total_work_hours / days_with_logs if days_with_logs > 0 else None
        average_break_hours_per_day = total_break_hours / days_with_logs if days_with_logs > 0 else None
        
        # Get current status (for specific user if provided)
        current_status = None
        if user_id:
            today = date.today()
            current_query = select(TimeLog).where(
                and_(
                    TimeLog.user_id == user_id,
                    TimeLog.log_date == today,
                    TimeLog.status.in_([TimeLogStatus.ACTIVE, TimeLogStatus.ON_BREAK])
                )
            )
            current_result = await db.execute(current_query)
            current_log = current_result.scalar_one_or_none()
            current_status = current_log.status if current_log else None
        
        # Get today's hours (for specific user if provided)
        today_work_hours = None
        today_break_hours = None
        if user_id:
            today = date.today()
            today_query = select(TimeLog).where(
                and_(
                    TimeLog.user_id == user_id,
                    TimeLog.log_date == today
                )
            )
            today_result = await db.execute(today_query)
            today_log = today_result.scalar_one_or_none()
            
            if today_log:
                if today_log.total_work_duration:
                    today_work_hours = today_log.total_work_duration / 3600.0
                if today_log.total_break_duration:
                    today_break_hours = today_log.total_break_duration / 3600.0
        
        statistics = TimeLogStatistics(
            total_work_hours=total_work_hours,
            total_break_hours=total_break_hours,
            total_days=total_days,
            average_hours_per_day=average_hours_per_day,
            average_break_hours_per_day=average_break_hours_per_day,
            days_with_logs=days_with_logs,
            current_status=current_status,
            today_work_hours=today_work_hours,
            today_break_hours=today_break_hours
        )
        
        log_info(f"Admin statistics retrieved for user {current_user.email}")
        return statistics
        
    except Exception as e:
        log_error(f"Error retrieving admin statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

