"""
Scheduler module for automated tasks.
Handles scheduled jobs like auto clock-out for employees who forgot to clock out.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date, timezone, time as dt_time, timedelta
from typing import Optional, List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from zoneinfo import ZoneInfo
from app.database import AsyncSessionLocal
from app.models import TimeTracker, TrackerStatus
from app.logger import log_info, log_error
import json

# IST timezone
IST = ZoneInfo("Asia/Kolkata")


def parse_pause_periods(pause_periods_json: Optional[str]) -> List[Dict]:
    """Parse pause periods JSON string to list of dicts."""
    if not pause_periods_json:
        return []
    try:
        return json.loads(pause_periods_json)
    except (json.JSONDecodeError, TypeError):
        return []


def serialize_pause_periods(pause_periods: List[Dict]) -> Optional[str]:
    """Serialize pause periods list to JSON string."""
    if not pause_periods:
        return None
    return json.dumps(pause_periods)


def ensure_timezone_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensure datetime is timezone-aware. If naive, assume UTC.
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # If naive, assume it's UTC
        return dt.replace(tzinfo=timezone.utc)
    
    return dt


def calculate_work_time(clock_in: datetime, clock_out: Optional[datetime], pause_periods: List[Dict], current_time: Optional[datetime] = None) -> Tuple[int, int]:
    """
    Calculate total work seconds and pause seconds.
    Returns: (total_work_seconds, total_pause_seconds)
    """
    # Ensure all datetimes are timezone-aware
    clock_in = ensure_timezone_aware(clock_in)
    clock_out = ensure_timezone_aware(clock_out)
    current_time = ensure_timezone_aware(current_time)
    
    end_time = clock_out or current_time or datetime.now(timezone.utc)
    
    if not clock_in:
        return (0, 0)
    
    # Total elapsed time
    total_elapsed = (end_time - clock_in).total_seconds()
    
    # Calculate total pause time
    total_pause = 0
    for pause in pause_periods:
        pause_start_str = pause.get('pause_start')
        pause_end_str = pause.get('pause_end')
        
        if pause_start_str:
            if isinstance(pause_start_str, str):
                pause_start = datetime.fromisoformat(pause_start_str.replace('Z', '+00:00'))
            else:
                pause_start = pause_start_str
            
            # Ensure timezone-aware
            pause_start = ensure_timezone_aware(pause_start)
            pause_end = None
            
            if pause_end_str:
                if isinstance(pause_end_str, str):
                    pause_end = datetime.fromisoformat(pause_end_str.replace('Z', '+00:00'))
                else:
                    pause_end = pause_end_str
                pause_end = ensure_timezone_aware(pause_end)
            elif not clock_out:  # If session is still active and pause is open
                pause_end = end_time
            
            if pause_end and pause_start:
                total_pause += (pause_end - pause_start).total_seconds()
    
    total_work = max(0, total_elapsed - total_pause)
    return (int(total_work), int(total_pause))


async def auto_clock_out_forgotten_sessions():
    """
    Automatically clock out all employees who forgot to clock out.
    This function runs daily at 11:00 PM IST and clocks out both previous day's and current day's forgotten sessions.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Get current time in UTC and IST
            now_utc = datetime.now(timezone.utc)
            now_ist = now_utc.astimezone(IST)
            today_ist = now_ist.date()
            yesterday_ist = today_ist - timedelta(days=1)
            
            log_info(f"Starting auto clock-out job at {now_utc} UTC ({now_ist} IST)")
            
            # Find all active or paused sessions from previous day and current day that haven't been clocked out
            # Use IST date for matching since trackers are stored with IST date
            result = await db.execute(
                select(TimeTracker)
                .where(
                    and_(
                        TimeTracker.date.in_([yesterday_ist, today_ist]),
                        TimeTracker.status.in_([TrackerStatus.ACTIVE, TrackerStatus.PAUSED]),
                        TimeTracker.clock_out.is_(None)
                    )
                )
            )
            trackers = result.scalars().all()
            
            if not trackers:
                log_info("No forgotten clock-out sessions found")
                return
            
            log_info(f"Found {len(trackers)} forgotten clock-out session(s)")
            
            clocked_out_count = 0
            for tracker in trackers:
                try:
                    # Set clock-out to exactly 11:00 PM IST of the tracker's date
                    # This ensures consistent behavior regardless of server timezone (local IST vs production UTC)
                    clock_out_time_ist = datetime.combine(
                        tracker.date,  # Use tracker's date
                        dt_time(23, 0, 0)  # Set to 11:00 PM
                    )
                    clock_out_time_ist = clock_out_time_ist.replace(tzinfo=IST)
                    clock_out_time_utc = clock_out_time_ist.astimezone(timezone.utc)
                    
                    # Log context per tracker
                    if tracker.date == yesterday_ist:
                        log_info(
                            f"Processing previous day tracker (tracker_id {tracker.id}) - clocking out at 11:00 PM IST "
                            f"on {tracker.date} ({clock_out_time_utc} UTC)"
                        )
                    else:
                        log_info(
                            f"Processing current day tracker (tracker_id {tracker.id}) - clocking out at 11:00 PM IST "
                            f"on {tracker.date} ({clock_out_time_utc} UTC)"
                        )
                    
                    # Close any open pause periods
                    pause_periods = parse_pause_periods(tracker.pause_periods)
                    if pause_periods and len(pause_periods) > 0 and pause_periods[-1].get('pause_end') is None:
                        pause_periods[-1]["pause_end"] = clock_out_time_utc.isoformat()
                    
                    # Ensure clock_in is timezone-aware before calculation
                    clock_in_aware = ensure_timezone_aware(tracker.clock_in)
                    
                    # Calculate final totals
                    total_work, total_pause = calculate_work_time(clock_in_aware, clock_out_time_utc, pause_periods, clock_out_time_utc)
                    
                    # Update tracker
                    tracker.clock_out = clock_out_time_utc
                    tracker.status = TrackerStatus.COMPLETED
                    tracker.pause_periods = serialize_pause_periods(pause_periods)
                    tracker.total_work_seconds = total_work
                    tracker.total_pause_seconds = total_pause
                    tracker.updated_at = clock_out_time_utc
                    
                    clocked_out_count += 1
                    log_info(f"Auto clocked out user_id {tracker.user_id} (tracker_id {tracker.id}, date: {tracker.date}) at {clock_out_time_utc} UTC ({clock_out_time_ist} IST), worked {total_work} seconds ({total_work/3600:.2f} hours)")
                    
                except Exception as e:
                    log_error(f"Error auto clocking out tracker_id {tracker.id}: {str(e)}", exc_info=e)
                    continue
            
            # Commit all changes
            await db.commit()
            log_info(f"Auto clock-out job completed. Successfully clocked out {clocked_out_count} session(s)")
            
        except Exception as e:
            log_error(f"Error in auto clock-out job: {str(e)}", exc_info=e)
            await db.rollback()
            raise


# Create scheduler instance with proper configuration
scheduler = AsyncIOScheduler(
    timezone="Asia/Kolkata",
    job_defaults={
        'coalesce': False,
        'max_instances': 1,
        'misfire_grace_time': 30
    }
)


def start_scheduler():
    """Start the scheduler with all scheduled jobs."""
    try:
        # Check if scheduler is already running
        if scheduler.running:
            log_info("Scheduler is already running")
            return
        
        # Schedule auto clock-out job to run daily at 11:00 PM IST
        scheduler.add_job(
            auto_clock_out_forgotten_sessions,
            trigger=CronTrigger(hour=23, minute=0, timezone="Asia/Kolkata"),
            id="auto_clock_out_daily",
            name="Auto Clock Out Forgotten Sessions",
            replace_existing=True
        )
        
        # Start the scheduler
        scheduler.start()
        
        # Verify scheduler started
        if scheduler.running:
            log_info("Scheduler started successfully - Auto clock-out job scheduled for 11:00 PM IST daily")
            
            # Log next run time
            job = scheduler.get_job("auto_clock_out_daily")
            if job:
                next_run = job.next_run_time
                log_info(f"Next scheduled run: {next_run}")
            else:
                log_error("Job not found after scheduling")
        else:
            log_error("Failed to start scheduler - scheduler is not running")
            
    except Exception as e:
        log_error(f"Error starting scheduler: {str(e)}", exc_info=e)
        raise


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        log_info("Scheduler shut down")

