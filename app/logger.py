import logging
import sys
import traceback
from datetime import datetime
from typing import Optional
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configure separate loggers for error and success logs
error_logger = logging.getLogger("hrms_error")
success_logger = logging.getLogger("hrms_success")

# Remove existing handlers to avoid duplicates
error_logger.handlers.clear()
success_logger.handlers.clear()

# Set log levels
error_logger.setLevel(logging.ERROR)
success_logger.setLevel(logging.INFO)

# Create file handlers
error_handler = logging.FileHandler(LOG_DIR / "error.log", encoding='utf-8')
success_handler = logging.FileHandler(LOG_DIR / "success.log", encoding='utf-8')

# Create console handler for errors (optional - for development)
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.ERROR)

# Create formatters
error_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - [%(module)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
success_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - [%(module)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Set formatters
error_handler.setFormatter(error_formatter)
success_handler.setFormatter(success_formatter)
console_handler.setFormatter(error_formatter)

# Add handlers to loggers
error_logger.addHandler(error_handler)
error_logger.addHandler(console_handler)
success_logger.addHandler(success_handler)

# Prevent propagation to root logger
error_logger.propagate = False
success_logger.propagate = False


def log_info(
    message: str,
    module: Optional[str] = None,
    user_id: Optional[int] = None,
    request_path: Optional[str] = None,
    request_method: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """Log success/info message to success.log file."""
    try:
        # Build log message with context
        log_parts = [message]
        
        if module:
            log_parts.append(f"[Module: {module}]")
        if user_id:
            log_parts.append(f"[User ID: {user_id}]")
        if request_path:
            log_parts.append(f"[Path: {request_method or 'N/A'} {request_path}]")
        if ip_address:
            log_parts.append(f"[IP: {ip_address}]")
        
        log_message = " | ".join(log_parts)
        success_logger.info(log_message)
    except Exception as e:
        # Fallback to console if file logging fails
        print(f"Failed to log success message: {str(e)}", file=sys.stderr)


def log_error(
    message: str,
    module: Optional[str] = None,
    user_id: Optional[int] = None,
    error_details: Optional[str] = None,
    request_path: Optional[str] = None,
    request_method: Optional[str] = None,
    ip_address: Optional[str] = None,
    exc_info: Optional[Exception] = None
):
    """Log error message to error.log file."""
    try:
        # Build log message with context
        log_parts = [message]
        
        if module:
            log_parts.append(f"[Module: {module}]")
        if user_id:
            log_parts.append(f"[User ID: {user_id}]")
        if request_path:
            log_parts.append(f"[Path: {request_method or 'N/A'} {request_path}]")
        if ip_address:
            log_parts.append(f"[IP: {ip_address}]")
        if error_details:
            log_parts.append(f"[Details: {error_details}]")
        
        log_message = " | ".join(log_parts)
        
        # Log with exception info if provided
        if exc_info:
            error_logger.error(log_message, exc_info=exc_info)
        else:
            error_logger.error(log_message)
    except Exception as e:
        # Fallback to console if file logging fails
        print(f"Failed to log error message: {str(e)}", file=sys.stderr)
        if exc_info:
            traceback.print_exc()


def log_warning(message: str, module: Optional[str] = None):
    """Log warning message to error.log file."""
    try:
        log_message = f"{message} | [Module: {module}]" if module else message
        error_logger.warning(log_message)
    except Exception as e:
        print(f"Failed to log warning: {str(e)}", file=sys.stderr)
