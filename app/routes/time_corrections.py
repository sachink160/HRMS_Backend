from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, func, select
from typing import List, Optional
from datetime import date, datetime, timedelta
import json

from app.database import get_db
from app.models import (
    User, TimeTracker, TimeCorrectionRequest, TimeCorrectionRequestStatus,
    TimeCorrectionLog, UserRole
)
from app.schema import (
    TimeCorrectionRequestCreate, TimeCorrectionRequestResponse,
    TimeCorrectionRequestUpdate, TimeCorrectionLogResponse
)
from app.routes.auth import get_current_user, get_current_admin_user
from app.logger import log_info, log_error
from app.timezone_utils import ensure_timezone_aware, IST

router = APIRouter(
    prefix="/time-corrections",
    tags=["Time Corrections"]
)

# --- User Endpoints ---

@router.post("/", response_model=TimeCorrectionRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_time_correction_request(
    request: TimeCorrectionRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a new time correction request.
    """
    # Check if request already exists for this date and is pending
    result = await db.execute(
        select(TimeCorrectionRequest).where(
            TimeCorrectionRequest.user_id == current_user.id,
            TimeCorrectionRequest.request_date == request.request_date,
            TimeCorrectionRequest.status == TimeCorrectionRequestStatus.PENDING
        )
    )
    existing_request = result.scalars().first()
    
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pending request already exists for this date"
        )
    
    # Get existing tracker record if any
    result = await db.execute(
        select(TimeTracker).where(
            TimeTracker.user_id == current_user.id,
            TimeTracker.date == request.request_date
        )
    )
    tracker = result.scalars().first()
    
    # If tracker_id is provided in the request, use that specific tracker
    # Otherwise, use the first one found (backward compatibility)
    if hasattr(request, 'tracker_id') and request.tracker_id:
        result = await db.execute(
            select(TimeTracker).where(
                TimeTracker.id == request.tracker_id,
                TimeTracker.user_id == current_user.id
            )
        )
        tracker = result.scalars().first()
        if not tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified tracker entry not found"
            )
    
    # Fetch ALL tracker entries for this date to check for overlaps
    result = await db.execute(
        select(TimeTracker).where(
            TimeTracker.user_id == current_user.id,
            TimeTracker.date == request.request_date
        ).order_by(TimeTracker.clock_in)
    )
    all_trackers = result.scalars().all()
    
    # Validate time overlap if we have requested times
    if request.requested_clock_in and request.requested_clock_out and len(all_trackers) > 1:
        # Ensure requested times are timezone-aware and convert to IST
        requested_in = ensure_timezone_aware(request.requested_clock_in).astimezone(IST)
        requested_out = ensure_timezone_aware(request.requested_clock_out).astimezone(IST)
        
        # Get the tracker_id we're correcting (if any)
        correcting_tracker_id = getattr(request, 'tracker_id', None) or (tracker.id if tracker else None)
        
        # Check for overlaps with other trackers
        for other_tracker in all_trackers:
            # Skip the tracker we're correcting
            if correcting_tracker_id and other_tracker.id == correcting_tracker_id:
                continue
                
            if other_tracker.clock_out:
                # Convert database times (UTC) to IST for accurate comparison
                other_start = ensure_timezone_aware(other_tracker.clock_in).astimezone(IST)
                other_end = ensure_timezone_aware(other_tracker.clock_out).astimezone(IST)
                
                # Check for overlap: requested_in < other_end AND requested_out > other_start
                if requested_in < other_end and requested_out > other_start:
                    # Format times for error message (all times now in IST)
                    conflict_start = other_start.strftime("%I:%M %p")
                    conflict_end = other_end.strftime("%I:%M %p")
                    requested_start_str = requested_in.strftime("%I:%M %p")
                    requested_end_str = requested_out.strftime("%I:%M %p")
                    
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Time conflict detected: Your requested time ({requested_start_str} - {requested_end_str}) overlaps with another tracker entry ({conflict_start} - {conflict_end}). Please adjust your times to avoid overlap."
                    )
    
    # Create request object
    new_request = TimeCorrectionRequest(
        user_id=current_user.id,
        tracker_id=getattr(request, 'tracker_id', None) or (tracker.id if tracker else None),
        request_date=request.request_date,
        issue_type=request.issue_type,
        requested_clock_in=request.requested_clock_in,
        requested_clock_out=request.requested_clock_out,
        requested_pause_periods=request.requested_pause_periods,
        reason=request.reason,
        status=TimeCorrectionRequestStatus.PENDING
    )

    # Early validation: Check if clock-out is before clock-in
    if request.requested_clock_in and request.requested_clock_out:
        normalized_in = ensure_timezone_aware(request.requested_clock_in).astimezone(IST)
        normalized_out = ensure_timezone_aware(request.requested_clock_out).astimezone(IST)
        
        if normalized_out <= normalized_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Clock-out time must be after clock-in time. Please check for AM/PM errors in your timeline."
            )

    # Business-rule validation for requested pause periods.
    # For 'forgot_resume', the user is defining a complete new timeline, so we just validate basic sanity.
    # For other issue types, we validate that breaks lie within the corrected clock-in/out window.
    if request.requested_pause_periods and request.issue_type != 'forgot_resume':
        # Normalize requested clock times to timezone-aware IST
        normalized_requested_in = ensure_timezone_aware(request.requested_clock_in).astimezone(IST) if request.requested_clock_in else None
        normalized_requested_out = ensure_timezone_aware(request.requested_clock_out).astimezone(IST) if request.requested_clock_out else None

        # Convert tracker times from UTC to IST
        tracker_clock_in = ensure_timezone_aware(tracker.clock_in).astimezone(IST) if tracker and tracker.clock_in else None
        tracker_clock_out = ensure_timezone_aware(tracker.clock_out).astimezone(IST) if tracker and tracker.clock_out else None
        
        # Determine effective clock window (prefer requested values, fall back to tracker)
        # For separate missed_clock_in/out (legacy) or unified missed_punch
        effective_clock_in = normalized_requested_in or tracker_clock_in
        effective_clock_out = normalized_requested_out or tracker_clock_out

        # Validation for missed_punch: Must have at least one valid clock time (and valid range if both exist)
        if request.issue_type == 'missed_punch':
            if not effective_clock_in and not effective_clock_out:
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="For Missed Punch, you must provide either a Clock In time or a Clock Out time."
                )

        if not (effective_clock_in and effective_clock_out):
            # If we are just correcting one side and the other doesn't exist yet (e.g. fresh day correction)?
            # Actually, standard logic requires both to validate breaks IN BETWEEN.
            # If we don't have both, we can't strict validate breaks fully, OR we skip break validation if breaks aren't being touched?
            # But here `request.requested_pause_periods` IS truthy, so user IS trying to modify breaks (or sending them back).
            pass 
            # We will raise error if we can't establish a window to validate breaks against
            # BUT: if it's a 'missed_punch' creating a brand new day (no tracker), and they provide breaks?
            # They should provide both IN and OUT if they want to validate breaks.
            
            if request.issue_type == 'missed_punch' and (not effective_clock_in or not effective_clock_out):
                 # If user provides breaks, they must provide the full window
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="To validate pause periods, both Clock In and Clock Out times are required."
                 )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot validate break periods without both clock in and clock out times."
            )

        try:
            if isinstance(request.requested_pause_periods, str):
                periods = json.loads(request.requested_pause_periods)
            else:
                periods = request.requested_pause_periods
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format for requested pause periods."
            )

        for p in periods or []:
            pause_start = p.get("pause_start")
            pause_end = p.get("pause_end")

            if not pause_start or not pause_end:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Both pause_start and pause_end are required for each break interval."
                )

            try:
                s_raw = datetime.fromisoformat(str(pause_start).replace("Z", "+00:00"))
                e_raw = datetime.fromisoformat(str(pause_end).replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pause period datetimes must be valid ISO 8601 strings."
                )

            # Normalise parsed pause datetimes to timezone-aware IST
            s_dt = ensure_timezone_aware(s_raw).astimezone(IST)
            e_dt = ensure_timezone_aware(e_raw).astimezone(IST)

            if e_dt < s_dt:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="pause_end cannot be before pause_start."
                )

            if s_dt < effective_clock_in or e_dt > effective_clock_out:
                # Format times for better error messages
                pause_start_str = s_dt.strftime("%I:%M %p")
                pause_end_str = e_dt.strftime("%I:%M %p")
                clock_in_str = effective_clock_in.strftime("%I:%M %p")
                clock_out_str = effective_clock_out.strftime("%I:%M %p")
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Break period ({pause_start_str} - {pause_end_str}) must lie within work hours ({clock_in_str} - {clock_out_str})."
                )
    
    # For 'forgot_resume', just do basic validation that pause periods are valid times
    elif request.requested_pause_periods and request.issue_type == 'forgot_resume':
        try:
            if isinstance(request.requested_pause_periods, str):
                periods = json.loads(request.requested_pause_periods)
            else:
                periods = request.requested_pause_periods
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format for requested pause periods."
            )

        for p in periods or []:
            pause_start = p.get("pause_start")
            pause_end = p.get("pause_end")

            if not pause_start or not pause_end:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Both pause_start and pause_end are required for each break interval."
                )

            try:
                s_raw = datetime.fromisoformat(str(pause_start).replace("Z", "+00:00"))
                e_raw = datetime.fromisoformat(str(pause_end).replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pause period datetimes must be valid ISO 8601 strings."
                )

            # Just validate that end is after start (normalize to IST)
            s_dt = ensure_timezone_aware(s_raw).astimezone(IST)
            e_dt = ensure_timezone_aware(e_raw).astimezone(IST)

            if e_dt <= s_dt:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Break end time must be after start time."
                )
    
    # Fill current values if tracker exists
    if tracker:
        new_request.current_clock_in = tracker.clock_in
        new_request.current_clock_out = tracker.clock_out
        new_request.current_pause_periods = tracker.pause_periods
    
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)
    
    # Create log entry
    log_entry = TimeCorrectionLog(
        request_id=new_request.id,
        action="created",
        performed_by=current_user.id,
        notes="Request submitted"
    )
    db.add(log_entry)
    await db.commit()
    await db.refresh(new_request, attribute_names=["logs"])
    new_request.user = current_user
    
    log_info(f"User {current_user.id} submitted time correction request {new_request.id}")
    return new_request

@router.get("/me", response_model=List[TimeCorrectionRequestResponse])
async def get_my_requests(
    limit: int = 20,
    skip: int = 0,
    status_filter: Optional[TimeCorrectionRequestStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's time correction requests.
    """
    query = select(TimeCorrectionRequest).where(
        TimeCorrectionRequest.user_id == current_user.id
    ).options(
        selectinload(TimeCorrectionRequest.user),
        selectinload(TimeCorrectionRequest.reviewer),
        selectinload(TimeCorrectionRequest.logs).selectinload(TimeCorrectionLog.performer),
    )
    
    if status_filter:
        query = query.where(TimeCorrectionRequest.status == status_filter)
    
    # Order by request date desc
    query = query.order_by(desc(TimeCorrectionRequest.request_date)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    requests = result.scalars().all()
    return requests

@router.get("/{request_id}", response_model=TimeCorrectionRequestResponse)
async def get_request_details(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific request. Users can only see their own. Admins can see all.
    """
    result = await db.execute(
        select(TimeCorrectionRequest)
        .options(
            selectinload(TimeCorrectionRequest.user),
            selectinload(TimeCorrectionRequest.reviewer),
            selectinload(TimeCorrectionRequest.logs).selectinload(TimeCorrectionLog.performer),
        )
        .where(TimeCorrectionRequest.id == request_id)
    )
    request = result.scalars().first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Access control
    if current_user.role != UserRole.ADMIN and request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this request"
        )
    
    return request

# --- Admin Endpoints ---

@router.get("/admin/all", response_model=List[TimeCorrectionRequestResponse])
async def get_all_requests(
    limit: int = 20,
    skip: int = 0,
    status_filter: Optional[TimeCorrectionRequestStatus] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin: Get all time correction requests with filtering.
    """
    query = select(TimeCorrectionRequest).options(
        selectinload(TimeCorrectionRequest.user),
        selectinload(TimeCorrectionRequest.reviewer),
        selectinload(TimeCorrectionRequest.logs).selectinload(TimeCorrectionLog.performer),
    )
    
    if status_filter:
        query = query.where(TimeCorrectionRequest.status == status_filter)
    
    if user_id:
        query = query.where(TimeCorrectionRequest.user_id == user_id)
    
    # Order by creation date desc by default to see newest first
    query = query.order_by(desc(TimeCorrectionRequest.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    requests = result.scalars().all()
    return requests

@router.patch("/admin/{request_id}/approve", response_model=TimeCorrectionRequestResponse)
async def approve_request(
    request_id: int,
    notes: TimeCorrectionRequestUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin: Approve a request and automatically update time records.
    """
    result = await db.execute(
        select(TimeCorrectionRequest)
        .options(
            selectinload(TimeCorrectionRequest.user),
            selectinload(TimeCorrectionRequest.reviewer),
            selectinload(TimeCorrectionRequest.logs).selectinload(TimeCorrectionLog.performer),
        )
        .where(TimeCorrectionRequest.id == request_id)
    )
    request = result.scalars().first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if request.status != TimeCorrectionRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Request is already {request.status}")

    # Start transaction logic
    try:
        # 1. Update Request Status
        request.status = TimeCorrectionRequestStatus.APPROVED
        request.admin_notes = notes.admin_notes
        request.reviewed_by = current_user.id
        request.reviewed_at = datetime.now()
        
        # 2. Update/Create TimeTracker
        result = await db.execute(
            select(TimeTracker).where(
                TimeTracker.user_id == request.user_id,
                TimeTracker.date == request.request_date
            )
        )
        tracker = result.scalars().first()
        
        old_tracker_values = {}
        new_tracker_values = {}
        
        if not tracker:
            # Create new tracker if supposed to be there but missing
            # Only if we have at least clock in data
            if request.requested_clock_in:
                tracker = TimeTracker(
                    user_id=request.user_id,
                    date=request.request_date,
                    clock_in=request.requested_clock_in,
                    clock_out=request.requested_clock_out,
                    pause_periods="[]",
                    status="completed" if request.requested_clock_out else "active"
                )
                db.add(tracker)
                await db.flush() # get ID
                request.tracker_id = tracker.id
                new_tracker_values = {
                    "clock_in": str(tracker.clock_in),
                    "clock_out": str(tracker.clock_out)
                }
        else:
            # Update existing tracker
            old_tracker_values = {
                "clock_in": str(tracker.clock_in),
                "clock_out": str(tracker.clock_out),
                "pause_periods": str(tracker.pause_periods)
            }
            
            # Update clock times if provided
            if request.requested_clock_in:
                tracker.clock_in = request.requested_clock_in
            if request.requested_clock_out:
                tracker.clock_out = request.requested_clock_out
                if tracker.status == "active":
                    tracker.status = "completed"
            
            # Update pause periods if provided (forgot_resume case)
            if request.requested_pause_periods:
                tracker.pause_periods = request.requested_pause_periods
                
            new_tracker_values = {
                "clock_in": str(tracker.clock_in),
                "clock_out": str(tracker.clock_out),
                "pause_periods": str(tracker.pause_periods)
            }

        # 3. Recalculate totals
        if tracker:
            recalculate_tracker_totals(tracker)
        
        # 4. Create Audit Log
        log_entry = TimeCorrectionLog(
            request_id=request.id,
            action="approved",
            performed_by=current_user.id,
            old_values=json.dumps(old_tracker_values),
            new_values=json.dumps(new_tracker_values),
            notes=notes.admin_notes or "Request approved"
        )
        db.add(log_entry)
        
        await db.commit()
        await db.refresh(request)
        return request
        
    except Exception as e:
        await db.rollback()
        log_error(f"Error approving time correction: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process approval")

@router.patch("/admin/{request_id}/reject", response_model=TimeCorrectionRequestResponse)
async def reject_request(
    request_id: int,
    notes: TimeCorrectionRequestUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin: Reject a request.
    """
    result = await db.execute(
        select(TimeCorrectionRequest)
        .options(
            selectinload(TimeCorrectionRequest.user),
            selectinload(TimeCorrectionRequest.reviewer),
            selectinload(TimeCorrectionRequest.logs).selectinload(TimeCorrectionLog.performer),
        )
        .where(TimeCorrectionRequest.id == request_id)
    )
    request = result.scalars().first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if request.status != TimeCorrectionRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Request is already {request.status}")
        
    if not notes.admin_notes:
        raise HTTPException(status_code=400, detail="Admin notes are required for rejection")

    request.status = TimeCorrectionRequestStatus.REJECTED
    request.admin_notes = notes.admin_notes
    request.reviewed_by = current_user.id
    request.reviewed_at = datetime.now()
    
    # Create Audit Log
    log_entry = TimeCorrectionLog(
        request_id=request.id,
        action="rejected",
        performed_by=current_user.id,
        notes=notes.admin_notes
    )
    db.add(log_entry)
    
    await db.commit()
    await db.refresh(request)
    return request

@router.get("/{request_id}/logs", response_model=List[TimeCorrectionLogResponse])
async def get_request_logs(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit logs for a request.
    """
    result = await db.execute(
        select(TimeCorrectionRequest)
        .options(
            selectinload(TimeCorrectionRequest.user),
        )
        .where(TimeCorrectionRequest.id == request_id)
    )
    request = result.scalars().first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    # Access control
    if current_user.role != UserRole.ADMIN and request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    result = await db.execute(
        select(TimeCorrectionLog)
        .options(
            selectinload(TimeCorrectionLog.performer),
        )
        .where(TimeCorrectionLog.request_id == request_id)
        .order_by(TimeCorrectionLog.created_at)
    )
    logs = result.scalars().all()
    
    return logs

# Helper function to recalculate work hours
def recalculate_tracker_totals(tracker: TimeTracker):
    """
    Recalculates total_work_seconds and total_pause_seconds based on clock_in, clock_out, and pause_periods.
    """
    if not tracker.clock_in:
        return
        
    duration = 0
    if tracker.clock_out:
        duration = int((tracker.clock_out - tracker.clock_in).total_seconds())
    else:
        # If still active, we can't fully calc total work, but we can calc pauses
        # Or maybe we just update pauses.
        # For historical corrections, usually clock_out is set. 
        # If active, work seconds depends on current time but usually stored as 0 until done?
        # Let's check existing logic. Usually we cal work = (out - in) - pauses
        pass
        
    # Pause calculation
    pause_seconds = 0
    if tracker.pause_periods:
        try:
            periods = json.loads(tracker.pause_periods)
            for p in periods:
                start = p.get('pause_start')
                end = p.get('pause_end')
                if start and end:
                    s_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    e_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    pause_seconds += int((e_dt - s_dt).total_seconds())
        except Exception as e:
            log_error(f"Error calculating pauses: {e}")
            
    tracker.total_pause_seconds = pause_seconds
    
    if tracker.clock_out:
        tracker.total_work_seconds = max(0, duration - pause_seconds)
