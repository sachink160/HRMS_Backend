from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, Query
from app.auth import get_current_admin_user
from app.logger import log_error
from app.response import APIResponse


router = APIRouter(prefix="/logs", tags=["logs"])

# Log file locations
LOG_DIR = Path("logs")
SUCCESS_LOG_PATH = LOG_DIR / "success.log"
ERROR_LOG_PATH = LOG_DIR / "error.log"


def _read_last_lines(path: Path, lines: int) -> List[str]:
    """
    Read the last `lines` lines from a log file.
    Falls back to an empty list if the file is missing.
    """
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            content = file.readlines()
        return [line.rstrip("\n") for line in content[-lines:]]
    except Exception as exc:
        # Log but return empty list to avoid crashing the endpoint
        log_error(f"Failed to read log file {path}: {exc}", module="logs")
        return []


@router.get("/success")
async def get_success_logs(
    lines: int = Query(100, ge=1, le=2000, description="Number of lines from the end of the success log"),
    # current_user=Depends(get_current_admin_user)
):
    """Return the latest success log entries."""
    log_lines = _read_last_lines(SUCCESS_LOG_PATH, lines)

    if not log_lines and not SUCCESS_LOG_PATH.exists():
        return APIResponse.not_found(message="Success log file not found")

    return APIResponse.success(
        data={
            "file": SUCCESS_LOG_PATH.name,
            "line_count": len(log_lines),
            "lines": log_lines
        },
        message="Success log retrieved"
    )


@router.get("/error")
async def get_error_logs(
    lines: int = Query(100, ge=1, le=2000, description="Number of lines from the end of the error log"),
    # current_user=Depends(get_current_admin_user)
):
    """Return the latest error log entries."""
    log_lines = _read_last_lines(ERROR_LOG_PATH, lines)

    if not log_lines and not ERROR_LOG_PATH.exists():
        return APIResponse.not_found(message="Error log file not found")

    return APIResponse.success(
        data={
            "file": ERROR_LOG_PATH.name,
            "line_count": len(log_lines),
            "lines": log_lines
        },
        message="Error log retrieved"
    )

