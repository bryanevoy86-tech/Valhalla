"""
Enhanced error logging and monitoring for API endpoints.
Provides structured logging for debugging and monitoring purposes.
"""

import logging
import traceback
import json
from typing import Any, Dict, Optional
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse

# Configure logger
logger = logging.getLogger(__name__)


class APIErrorLogger:
    """Centralized error logging for API endpoints."""
    
    @staticmethod
    def log_request_payload(endpoint: str, payload: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log API request payload for debugging.
        
        Args:
            endpoint: API endpoint path
            payload: Request payload
            metadata: Additional metadata to log
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": endpoint,
            "payload": payload,
        }
        
        if metadata:
            log_data.update(metadata)
        
        logger.info(f"API Request: {json.dumps(log_data, default=str)}")
    
    @staticmethod
    def log_api_error(endpoint: str, error: Exception, payload: Optional[Dict[str, Any]] = None, status_code: int = 500) -> None:
        """
        Log API error with full context.
        
        Args:
            endpoint: API endpoint path
            error: Exception that occurred
            payload: Request payload that caused the error
            status_code: HTTP status code
        """
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": endpoint,
            "status_code": status_code,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }
        
        if payload:
            error_data["payload"] = payload
        
        logger.error(f"API Error: {json.dumps(error_data, default=str)}")
    
    @staticmethod
    def log_validation_error(endpoint: str, field: str, error_message: str, received_value: Any = None) -> None:
        """
        Log validation errors.
        
        Args:
            endpoint: API endpoint path
            field: Field that failed validation
            error_message: Validation error message
            received_value: Value that failed validation
        """
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": endpoint,
            "validation_error": {
                "field": field,
                "message": error_message,
                "received_value": received_value,
            }
        }
        
        logger.warning(f"Validation Error: {json.dumps(error_data, default=str)}")
    
    @staticmethod
    def log_sanitization(endpoint: str, field: str, original: Any, sanitized: Any) -> None:
        """
        Log sanitization operations.
        
        Args:
            endpoint: API endpoint path
            field: Field that was sanitized
            original: Original value
            sanitized: Sanitized value
        """
        if original != sanitized:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "endpoint": endpoint,
                "field": field,
                "original": original,
                "sanitized": sanitized,
            }
            logger.info(f"Sanitization: {json.dumps(log_data, default=str)}")


class RequestLoggingMiddleware:
    """Middleware to log all incoming requests and responses."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        """Log request and response."""
        try:
            # Log request
            logger.info(
                f"Incoming request: {request.method} {request.url.path} | "
                f"Client: {request.client}"
            )
            
            # Process request
            response = await call_next(request)
            
            # Log response
            logger.info(
                f"Response sent: {request.method} {request.url.path} | "
                f"Status: {response.status_code}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Middleware error on {request.url.path}: {str(e)}", exc_info=True)
            raise


def create_error_response(error_code: str, message: str, details: Optional[Dict[str, Any]] = None, status_code: int = 400) -> JSONResponse:
    """
    Create standardized error response.
    
    Args:
        error_code: Error code for categorization
        message: Human-readable error message
        details: Additional error details
        status_code: HTTP status code
    
    Returns:
        JSONResponse with standardized error format
    """
    response_data = {
        "error": error_code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if details:
        response_data["details"] = details
    
    return JSONResponse(status_code=status_code, content=response_data)
