"""
PACK TW: Correlation ID & Request Context Middleware
Adds X-Request-ID / correlation_id for every request & response.
"""

import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique correlation_id to each request.
    Reads from X-Request-ID header if present, otherwise generates a UUID.
    Attaches to request.state.correlation_id for access in handlers/services.
    Returns correlation_id in response X-Request-ID header.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # 1. Try to read existing request ID from header
        incoming = request.headers.get("X-Request-ID")
        correlation_id = incoming or str(uuid.uuid4())

        # 2. Attach to request state so handlers/services can read it
        request.state.correlation_id = correlation_id

        # 3. Call downstream
        response = await call_next(request)

        # 4. Ensure response carries the same ID
        response.headers["X-Request-ID"] = correlation_id
        return response
