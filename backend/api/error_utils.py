"""
Standardized error response utilities for consistent error formatting across all routes.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException


def create_error_response(
    status_code: int,
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary.
    
    Args:
        status_code: HTTP status code
        error_type: Type of error (e.g., "ValidationError", "TimeoutError", "InternalServerError")
        message: Human-readable error message
        details: Optional additional error details
        timestamp: Optional ISO timestamp (defaults to current time)
    
    Returns:
        Standardized error response dictionary
    """
    return {
        "status": "error",
        "error": {
            "type": error_type,
            "message": message,
            "details": details or {},
            "timestamp": timestamp or datetime.utcnow().isoformat()
        }
    }


def raise_standardized_error(
    status_code: int,
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Raise an HTTPException with standardized error format.
    
    Args:
        status_code: HTTP status code
        error_type: Type of error
        message: Human-readable error message
        details: Optional additional error details
    
    Raises:
        HTTPException with standardized error detail
    """
    error_response = create_error_response(status_code, error_type, message, details)
    raise HTTPException(status_code=status_code, detail=error_response["error"])

