from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, date, timezone, timedelta
from typing import List, Optional
import json
from app.database import get_db
from app.models import User, TimeTracker, TrackerStatus
from app.timezone_utils import IST, ensure_timezone_aware, get_now_and_today_ist
from app.schema import (
    TrackerResponse, TrackerCurrentResponse, TrackerSummaryResponse,
    PaginationParams, PaginatedResponse, UserResponse
)
from app.auth import get_current_user
from app.logger import log_info, log_error
from app.response import APIResponse

router = APIRouter(prefix="/tracker", tags=["tracker"])

def parse_pause_periods(pause_periods_json: Optional[str]) -> List[dict]:
    """Parse pause periods JSON string to list of dicts."""
    if not pause_periods_json:
        return []
    try:
        return json.loads(pause_periods_json)
    except (json.JSONDecodeError, TypeError):
        return []

def serialize_pause_periods(pause_periods: List[dict]) -> str:
    """Serialize pause periods list to JSON string."""
    if not pause_periods:
        return None
    return json.dumps(pause_periods)

def calculate_work_time(clock_in: datetime, clock_out: Optional[datetime], pause_periods: List[dict], current_time: Optional[datetime] = None) -> tuple[int, int]:
    """
    Calculate total work seconds and pause seconds.
    Returns: (total_work_seconds, total_pause_seconds)
    """
    clock_in = ensure_timezone_aware(clock_in)
    clock_out = ensure_timezone_aware(clock_out)
    current_time = ensure_timezone_aware(current_time)

    end_time = clock_out or current_time or ensure_timezone_aware(datetime.now(timezone.utc))
    
    if not clock_in:
        return (0, 0)
    
    # Normalize to UTC for consistent math
    clock_in_utc = clock_in.astimezone(timezone.utc)
    end_time_utc = end_time.astimezone(timezone.utc)

    # Total elapsed time (clamped non-negative)
    total_elapsed = max(0, (end_time_utc - clock_in_utc).total_seconds())
    
    # Calculate total pause time (clamped to session window)
    total_pause = 0
    for pause in pause_periods:
        pause_start_str = pause.get('pause_start')
        pause_end_str = pause.get('pause_end')
        
        if not pause_start_str:
            continue

        pause_start = ensure_timezone_aware(pause_start_str)
        pause_end = ensure_timezone_aware(pause_end_str) if pause_end_str else None

        if not pause_end and not clock_out:
            # If session still active and pause is open, treat end as current end_time
            pause_end = end_time

        if not pause_start or not pause_end:
            continue

        pause_start_utc = pause_start.astimezone(timezone.utc)
        pause_end_utc = pause_end.astimezone(timezone.utc)

        # Clamp pause to the session window
        effective_start = max(clock_in_utc, pause_start_utc)
        effective_end = min(end_time_utc, pause_end_utc)

        if effective_end > effective_start:
            total_pause += (effective_end - effective_start).total_seconds()
    
    total_work = max(0, total_elapsed - total_pause)
    return (int(total_work), int(total_pause))

def tracker_to_dict(tracker: TimeTracker, include_user: bool = False) -> dict:
    """Convert TimeTracker model to dictionary for response."""
    pause_periods = parse_pause_periods(tracker.pause_periods)
    
    # Recalculate work and pause using normalized times to avoid stale/incorrect totals
    total_work_seconds, total_pause_seconds = calculate_work_time(
        tracker.clock_in,
        tracker.clock_out,
        pause_periods
    )
    total_work_hours = round(total_work_seconds / 3600, 2)
    
    result = {
        "id": tracker.id,
        "user_id": tracker.user_id,
        "date": tracker.date.isoformat() if tracker.date else None,
        "clock_in": tracker.clock_in.isoformat() if tracker.clock_in else None,
        "clock_out": tracker.clock_out.isoformat() if tracker.clock_out else None,
        "status": tracker.status.value if hasattr(tracker.status, 'value') else str(tracker.status),
        "pause_periods": pause_periods,
        "total_work_seconds": total_work_seconds,
        "total_pause_seconds": total_pause_seconds,
        "total_work_hours": total_work_hours,
        "created_at": tracker.created_at.isoformat() if tracker.created_at else None,
        "updated_at": tracker.updated_at.isoformat() if tracker.updated_at else None,
    }
    
    if include_user and tracker.user:
        result["user"] = {
            "id": tracker.user.id,
            "name": tracker.user.name,
            "email": tracker.user.email,
            "designation": tracker.user.designation,
        }
    
    return result

# Employee Endpoints

@router.post("/clock-in")
async def clock_in(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clock in - Start a new tracking session."""
    try:
        now, today = get_now_and_today_ist()
        
        # Check if user already has an active session today
        result = await db.execute(
            select(TimeTracker)
            .where(
                and_(
                    TimeTracker.user_id == current_user.id,
                    TimeTracker.date == today,
                    TimeTracker.status.in_([TrackerStatus.ACTIVE, TrackerStatus.PAUSED])
                )
            )
        )
        existing_tracker = result.scalar_one_or_none()
        
        if existing_tracker:
            log_error(f"User {current_user.email} attempted to clock in but already has active session")
            return APIResponse.bad_request(
                message="You already have an active tracking session. Please clock out first."
            )
        
        # Create new tracker entry
        tracker = TimeTracker(
            user_id=current_user.id,
            date=today,
            clock_in=now,
            status=TrackerStatus.ACTIVE,
            total_work_seconds=0,
            total_pause_seconds=0
        )
        
        db.add(tracker)
        await db.commit()
        await db.refresh(tracker)
        
        log_info(f"User {current_user.email} clocked in at {now}")
        
        return APIResponse.created(
            data=tracker_to_dict(tracker),
            message="Clocked in successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Clock in error: {str(e)}")
        await db.rollback()
        return APIResponse.internal_error(message="Failed to clock in")

@router.post("/pause")
async def pause(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pause current tracking session."""
    try:
        now, today = get_now_and_today_ist()
        
        # Find active session
        result = await db.execute(
            select(TimeTracker)
            .where(
                and_(
                    TimeTracker.user_id == current_user.id,
                    TimeTracker.date == today,
                    TimeTracker.status == TrackerStatus.ACTIVE
                )
            )
        )
        tracker = result.scalar_one_or_none()
        
        if not tracker:
            return APIResponse.bad_request(
                message="No active session found. Please clock in first."
            )
        
        # Check if there's already an open pause
        pause_periods = parse_pause_periods(tracker.pause_periods)
        if pause_periods and pause_periods[-1].get('pause_end') is None:
            return APIResponse.bad_request(
                message="Session is already paused. Please resume first."
            )
        
        # Add new pause period
        pause_periods.append({
            "pause_start": now.isoformat(),
            "pause_end": None
        })
        
        tracker.pause_periods = serialize_pause_periods(pause_periods)
        tracker.status = TrackerStatus.PAUSED
        tracker.updated_at = now
        
        await db.commit()
        await db.refresh(tracker)
        
        log_info(f"User {current_user.email} paused session at {now}")
        
        return APIResponse.success(
            data=tracker_to_dict(tracker),
            message="Session paused successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Pause error: {str(e)}")
        await db.rollback()
        return APIResponse.internal_error(message="Failed to pause session")

@router.post("/resume")
async def resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resume paused tracking session."""
    try:
        now, today = get_now_and_today_ist()
        
        # Find paused session
        result = await db.execute(
            select(TimeTracker)
            .where(
                and_(
                    TimeTracker.user_id == current_user.id,
                    TimeTracker.date == today,
                    TimeTracker.status == TrackerStatus.PAUSED
                )
            )
        )
        tracker = result.scalar_one_or_none()
        
        if not tracker:
            return APIResponse.bad_request(
                message="No paused session found. Please clock in first."
            )
        
        # Check if there's an open pause to close
        pause_periods = parse_pause_periods(tracker.pause_periods)
        if not pause_periods or pause_periods[-1].get('pause_end') is not None:
            return APIResponse.bad_request(
                message="Session is not paused. Please pause first."
            )
        
        # Close the last pause period
        pause_periods[-1]["pause_end"] = now.isoformat()
        
        tracker.pause_periods = serialize_pause_periods(pause_periods)
        tracker.status = TrackerStatus.ACTIVE
        tracker.updated_at = now
        
        await db.commit()
        await db.refresh(tracker)
        
        log_info(f"User {current_user.email} resumed session at {now}")
        
        return APIResponse.success(
            data=tracker_to_dict(tracker),
            message="Session resumed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Resume error: {str(e)}")
        await db.rollback()
        return APIResponse.internal_error(message="Failed to resume session")

@router.post("/clock-out")
async def clock_out(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clock out - End current tracking session."""
    try:
        now, today = get_now_and_today_ist()
        
        # Find active or paused session
        result = await db.execute(
            select(TimeTracker)
            .where(
                and_(
                    TimeTracker.user_id == current_user.id,
                    TimeTracker.date == today,
                    TimeTracker.status.in_([TrackerStatus.ACTIVE, TrackerStatus.PAUSED])
                )
            )
        )
        tracker = result.scalar_one_or_none()
        
        if not tracker:
            return APIResponse.bad_request(
                message="No active session found. Please clock in first."
            )
        
        # Close any open pause
        pause_periods = parse_pause_periods(tracker.pause_periods)
        if pause_periods and pause_periods[-1].get('pause_end') is None:
            pause_periods[-1]["pause_end"] = now.isoformat()
        
        # Calculate final totals
        total_work, total_pause = calculate_work_time(tracker.clock_in, now, pause_periods, now)
        
        tracker.clock_out = now
        tracker.status = TrackerStatus.COMPLETED
        tracker.pause_periods = serialize_pause_periods(pause_periods)
        tracker.total_work_seconds = total_work
        tracker.total_pause_seconds = total_pause
        tracker.updated_at = now
        
        await db.commit()
        await db.refresh(tracker)
        
        log_info(f"User {current_user.email} clocked out at {now}, worked {total_work} seconds")
        
        return APIResponse.success(
            data=tracker_to_dict(tracker),
            message="Clocked out successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Clock out error: {str(e)}")
        await db.rollback()
        return APIResponse.internal_error(message="Failed to clock out")

@router.get("/current")
async def get_current_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current active/paused session status."""
    try:
        _, today = get_now_and_today_ist()
        
        result = await db.execute(
            select(TimeTracker)
            .where(
                and_(
                    TimeTracker.user_id == current_user.id,
                    TimeTracker.date == today,
                    TimeTracker.status.in_([TrackerStatus.ACTIVE, TrackerStatus.PAUSED])
                )
            )
        )
        tracker = result.scalar_one_or_none()
        
        if not tracker:
            return APIResponse.success(
                data={
                    "has_active_session": False,
                    "tracker": None,
                    "current_work_seconds": None,
                    "current_pause_seconds": None
                },
                message="No active session"
            )
        
        # Calculate current work time
        pause_periods = parse_pause_periods(tracker.pause_periods)
        current_work, current_pause = calculate_work_time(tracker.clock_in, tracker.clock_out, pause_periods)
        
        return APIResponse.success(
            data={
                "has_active_session": True,
                "tracker": tracker_to_dict(tracker),
                "current_work_seconds": current_work,
                "current_pause_seconds": current_pause
            },
            message="Current session retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get current session error: {str(e)}")
        return APIResponse.internal_error(message="Failed to get current session")

@router.get("/my-history")
async def get_my_history(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    status_filter: Optional[str] = Query(None, description="Status filter: active, paused, completed"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get employee's own tracking history."""
    try:
        query = select(TimeTracker).where(TimeTracker.user_id == current_user.id)
        
        # Apply filters
        if start_date:
            query = query.where(TimeTracker.date >= start_date)
        if end_date:
            query = query.where(TimeTracker.date <= end_date)
        if status_filter:
            try:
                status_enum = TrackerStatus(status_filter.lower())
                query = query.where(TimeTracker.status == status_enum)
            except ValueError:
                pass
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply ordering
        query = query.order_by(TimeTracker.date.desc(), TimeTracker.created_at.desc())
        
        result = await db.execute(query)
        trackers = result.scalars().all()
        
        trackers_data = [tracker_to_dict(tracker) for tracker in trackers]
        
        return APIResponse.success(
            data={
                "items": trackers_data,
                "total": total
            },
            message="Tracking history retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get history error: {str(e)}")
        return APIResponse.internal_error(message="Failed to fetch tracking history")

@router.get("/by-date")
async def get_trackers_by_date(
    date_param: date = Query(..., alias="date", description="Date to fetch trackers for (YYYY-MM-DD)"),
    user_id: Optional[int] = Query(None, description="User ID (optional, admin use)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all tracker entries for a specific date.
    Useful for time correction when multiple entries exist for the same day.
    """
    try:
        # If user_id is provided and user is not admin, only allow fetching own data
        target_user_id = user_id if user_id and current_user.role.value == "admin" else current_user.id
        
        # Fetch all trackers for the given date
        query = select(TimeTracker).where(
            and_(
                TimeTracker.user_id == target_user_id,
                TimeTracker.date == date_param
            )
        ).order_by(TimeTracker.clock_in.asc())
        
        result = await db.execute(query)
        trackers = result.scalars().all()
        
        trackers_data = [tracker_to_dict(tracker) for tracker in trackers]
        
        log_info(f"Fetched {len(trackers_data)} tracker(s) for user {target_user_id} on {date_param}")
        
        return APIResponse.success(
            data=trackers_data,
            message=f"Found {len(trackers_data)} tracker entry(ies) for the selected date"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get trackers by date error: {str(e)}", exc_info=e)
        return APIResponse.internal_error(message="Failed to fetch trackers for the specified date")

# Admin endpoints moved to admin.py router at /admin/tracker/*

