"""
Custom Exception Handlers

This module provides custom exception handlers for FastAPI
to ensure all errors follow the standardized response format.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.response import APIResponse
from app.logger import log_error
from typing import Union


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTPException and convert to standardized format.
    
    Args:
        request: FastAPI request object
        exc: HTTPException instance
        
    Returns:
        JSONResponse with standardized error format
    """
    status_code = exc.status_code
    detail = exc.detail
    
    # Map status codes to appropriate error messages
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return APIResponse.unauthorized(
            message=str(detail) if detail else "Authentication required"
        )
    elif status_code == status.HTTP_403_FORBIDDEN:
        return APIResponse.forbidden(
            message=str(detail) if detail else "Insufficient permissions"
        )
    elif status_code == status.HTTP_404_NOT_FOUND:
        return APIResponse.not_found(
            message=str(detail) if detail else "Resource not found"
        )
    elif status_code == status.HTTP_400_BAD_REQUEST:
        return APIResponse.bad_request(
            message=str(detail) if detail else "Invalid request"
        )
    elif status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        return APIResponse.validation_error(
            errors={"detail": str(detail)} if isinstance(detail, str) else detail,
            message="Validation failed"
        )
    else:
        return APIResponse.error(
            message=str(detail) if detail else "An error occurred",
            status_code=status_code
        )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle RequestValidationError and convert to standardized format.
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError instance
        
    Returns:
        JSONResponse with standardized validation error format
    """
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        errors[field] = error.get("msg", "Validation error")
    
    log_error(f"Validation error: {errors}")
    
    return APIResponse.validation_error(
        errors=errors,
        message="Request validation failed"
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions and convert to standardized format.
    
    Args:
        request: FastAPI request object
        exc: Exception instance
        
    Returns:
        JSONResponse with standardized error format
    """
    log_error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return APIResponse.internal_error(
        message="An unexpected error occurred. Please try again later.",
        data={"error_type": type(exc).__name__}
    )

