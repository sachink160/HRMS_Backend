from datetime import datetime, timezone
from typing import Optional

from zoneinfo import ZoneInfo

# Canonical business timezone for the application (India Standard Time).
IST = ZoneInfo("Asia/Kolkata")


def ensure_timezone_aware(
    dt: Optional[datetime] | str,
    assume_tz: timezone | ZoneInfo = IST,
) -> Optional[datetime]:
    """
    Normalize a datetime (or ISO string) to a timezone-aware value.

    - If dt is None, returns None.
    - If dt is a string, attempts to parse it as ISO 8601 (accepts a trailing 'Z').
    - If dt is naive (no tzinfo), attaches the provided assume_tz (IST by default).
    - If dt is already timezone-aware, returns it unchanged.
    """
    if dt is None:
        return None

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=assume_tz)

    return dt


def get_now_and_today_ist() -> tuple[datetime, datetime.date]:
    """
    Return the current time and date in IST.

    The underlying clock uses UTC and then converts to IST, so behavior is
    consistent regardless of the server's local timezone settings.
    """
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST)
    today_ist = now_ist.date()
    return now_ist, today_ist

