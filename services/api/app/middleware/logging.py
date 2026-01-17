# services/api/app/middleware/logging.py

"""
Request/response logging middleware for PACK T: Production Hardening.
Logs HTTP request details and response times.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("valhalla.api.requests")
logger.setLevel(logging.INFO)

# Ensure we have a handler if none is configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log HTTP requests and response times.
    Useful for debugging, monitoring, and performance analysis.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Record start time
        start_time = time.time()
        
        # Get request details
        method = request.method
        path = request.url.path
        
        # Call the next middleware/handler
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log the request and response
        logger.info(
            "%s %s - %s (%0.2fms)",
            method,
            path,
            response.status_code,
            duration_ms,
        )
        
        return response
