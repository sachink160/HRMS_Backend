"""
Standardized API Response Utility

This module provides utilities for creating consistent API responses
across all endpoints in the HRMS backend.

Response Format:
{
    "status": "success" | "error",
    "message": "Human-readable message",
    "data": {
        // Response data (can be any structure)
    }
}
"""

from typing import Any, Optional, Dict
from fastapi import status
from fastapi.responses import JSONResponse


class APIResponse:
    """Standardized API Response class"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Operation completed successfully",
        status_code: int = status.HTTP_200_OK
    ) -> JSONResponse:
        """
        Create a successful API response.
        
        Args:
            data: The response data (can be dict, list, model, etc.)
            message: Success message
            status_code: HTTP status code (default: 200)
            
        Returns:
            JSONResponse with standardized format
        """
        response_data = {
            "status": "success",
            "message": message,
            "data": data if data is not None else {}
        }
        return JSONResponse(content=response_data, status_code=status_code)
    
    @staticmethod
    def error(
        message: str = "An error occurred",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ) -> JSONResponse:
        """
        Create an error API response.
        
        Args:
            message: Error message
            status_code: HTTP status code (default: 400)
            data: Additional error data (optional)
            error_code: Error code for programmatic handling (optional)
            
        Returns:
            JSONResponse with standardized error format
        """
        error_data = {
            "status": "error",
            "message": message,
            "data": data if data is not None else {}
        }
        
        if error_code:
            error_data["error_code"] = error_code
        
        return JSONResponse(content=error_data, status_code=status_code)
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = "Resource created successfully"
    ) -> JSONResponse:
        """Create a 201 Created response."""
        return APIResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED
        )
    
    @staticmethod
    def not_found(
        message: str = "Resource not found",
        resource: Optional[str] = None
    ) -> JSONResponse:
        """Create a 404 Not Found response."""
        data = {}
        if resource:
            data["resource"] = resource
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            data=data,
            error_code="NOT_FOUND"
        )
    
    @staticmethod
    def unauthorized(
        message: str = "Authentication required"
    ) -> JSONResponse:
        """Create a 401 Unauthorized response."""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED"
        )
    
    @staticmethod
    def forbidden(
        message: str = "Insufficient permissions"
    ) -> JSONResponse:
        """Create a 403 Forbidden response."""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN"
        )
    
    @staticmethod
    def bad_request(
        message: str = "Invalid request",
        data: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Create a 400 Bad Request response."""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=data,
            error_code="BAD_REQUEST"
        )
    
    @staticmethod
    def validation_error(
        errors: Dict[str, Any],
        message: str = "Validation failed"
    ) -> JSONResponse:
        """Create a 422 Validation Error response."""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            data={"validation_errors": errors},
            error_code="VALIDATION_ERROR"
        )
    
    @staticmethod
    def internal_error(
        message: str = "Internal server error",
        data: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Create a 500 Internal Server Error response."""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=data,
            error_code="INTERNAL_ERROR"
        )

