"""
PACK L0-06: Correlation ID Middleware
Automatically injects correlation IDs into all requests and responses.
Enables distributed tracing across services.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from uuid import uuid4
import contextvars


# Context variable to store correlation ID for current request
request_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> str:
    """Get correlation ID from context (for use in application code)."""
    cid = request_correlation_id.get()
    return cid or str(uuid4())


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds correlation ID to all requests and responses.
    
    If X-Correlation-ID header is present, uses that value.
    Otherwise, generates a new UUID.
    
    This correlation ID is:
    - Added to all responses as X-Correlation-ID header
    - Stored in context variable for use in application code
    - Should be used by services when writing logs/telemetry
    - Should be propagated when calling downstream services
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Inject or extract correlation ID from request.
        
        Args:
            request: FastAPI Request
            call_next: Next middleware/endpoint
        
        Returns:
            Response with X-Correlation-ID header
        """
        # Extract correlation ID from request or generate new one
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid4())
        
        # Store in context for application code to access
        request_correlation_id.set(correlation_id)
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
