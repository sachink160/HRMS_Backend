"""
Scheduler module for automated tasks.
Handles scheduled jobs like auto clock-out for employees who forgot to clock out.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date, timezone, time as dt_time
from typing import Optional, List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import AsyncSessionLocal
from app.models import TimeTracker, TrackerStatus
from app.logger import log_info, log_error
import json


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


def calculate_work_time(clock_in: datetime, clock_out: Optional[datetime], pause_periods: List[Dict], current_time: Optional[datetime] = None) -> Tuple[int, int]:
    """
    Calculate total work seconds and pause seconds.
    Returns: (total_work_seconds, total_pause_seconds)
    """
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
            pause_start = datetime.fromisoformat(pause_start_str.replace('Z', '+00:00')) if isinstance(pause_start_str, str) else pause_start_str
            pause_end = None
            
            if pause_end_str:
                pause_end = datetime.fromisoformat(pause_end_str.replace('Z', '+00:00')) if isinstance(pause_end_str, str) else pause_end_str
            elif not clock_out:  # If session is still active and pause is open
                pause_end = end_time
            
            if pause_end:
                total_pause += (pause_end - pause_start).total_seconds()
    
    total_work = max(0, total_elapsed - total_pause)
    return (int(total_work), int(total_pause))


async def auto_clock_out_forgotten_sessions():
    """
    Automatically clock out all employees who forgot to clock out.
    This function runs daily at 11:55 PM.
    """
    db: AsyncSession = AsyncSessionLocal()
    try:
        now = datetime.now(timezone.utc)
        today = now.date()
        
        # Set clock out time to 11:55 PM of the current day (or end of day)
        # Using 23:55:00 UTC (adjust timezone if needed)
        clock_out_time = datetime.combine(today, dt_time(23, 55, 0)).replace(tzinfo=timezone.utc)
        
        # If current time is before 11:55 PM, use current time instead
        if now < clock_out_time:
            clock_out_time = now
        
        log_info(f"Starting auto clock-out job at {now}. Clock out time set to {clock_out_time}")
        
        # Find all active or paused sessions that haven't been clocked out
        result = await db.execute(
            select(TimeTracker)
            .where(
                and_(
                    TimeTracker.date == today,
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
                # Close any open pause periods
                pause_periods = parse_pause_periods(tracker.pause_periods)
                if pause_periods and pause_periods[-1].get('pause_end') is None:
                    pause_periods[-1]["pause_end"] = clock_out_time.isoformat()
                
                # Calculate final totals
                total_work, total_pause = calculate_work_time(tracker.clock_in, clock_out_time, pause_periods, clock_out_time)
                
                # Update tracker
                tracker.clock_out = clock_out_time
                tracker.status = TrackerStatus.COMPLETED
                tracker.pause_periods = serialize_pause_periods(pause_periods)
                tracker.total_work_seconds = total_work
                tracker.total_pause_seconds = total_pause
                tracker.updated_at = clock_out_time
                
                clocked_out_count += 1
                log_info(f"Auto clocked out user_id {tracker.user_id} (tracker_id {tracker.id}) at {clock_out_time}, worked {total_work} seconds")
                
            except Exception as e:
                log_error(f"Error auto clocking out tracker_id {tracker.id}: {str(e)}")
                continue
        
        # Commit all changes
        await db.commit()
        log_info(f"Auto clock-out job completed. Successfully clocked out {clocked_out_count} session(s)")
        
    except Exception as e:
        log_error(f"Error in auto clock-out job: {str(e)}")
        await db.rollback()
    finally:
        await db.close()


# Create scheduler instance
scheduler = AsyncIOScheduler()


def start_scheduler():
    """Start the scheduler with all scheduled jobs."""
    # Schedule auto clock-out job to run daily at 11:55 PM
    scheduler.add_job(
        auto_clock_out_forgotten_sessions,
        trigger=CronTrigger(hour=23, minute=55, timezone="Asia/Kolkata"),
        id="auto_clock_out_daily",
        name="Auto Clock Out Forgotten Sessions",
        replace_existing=True
    )
    
    scheduler.start()
    log_info("Scheduler started - Auto clock-out job scheduled for 11:55 PM daily")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        log_info("Scheduler shut down")

