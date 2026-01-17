# services/api/app/middleware/security.py

"""
Security middleware for PACK T: Production Hardening.
Adds security headers and basic rate limiting.
"""

from __future__ import annotations

import time
from typing import Callable, Dict, List

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# In-memory rate limit store: tracks request timestamps per client:path
# For production, swap this out for Redis or similar distributed store
_rate_limit_store: Dict[str, List[float]] = {}

MAX_REQUESTS = 100      # Max requests allowed
WINDOW_SECONDS = 60.0   # Per time window (1 minute)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    Helps protect against common web vulnerabilities.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Referrer policy: don't send referrer to other sites
        response.headers["Referrer-Policy"] = "no-referrer"
        
        # XSS Protection (legacy, but good for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Strict Transport Security (HSTS) - uncomment if using HTTPS
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-process rate limiting per IP and path.
    Allows MAX_REQUESTS per WINDOW_SECONDS per unique client:path combination.
    
    WARNING: This is for development/small deployments only.
    For production, use a distributed solution (Redis, cloud service, etc.).
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Key combining IP and path
        key = f"{client_ip}:{request.url.path}"
        
        now = time.time()
        
        # Get or initialize bucket for this client:path
        bucket = _rate_limit_store.get(key, [])
        
        # Remove old timestamps outside the window
        bucket = [ts for ts in bucket if now - ts < WINDOW_SECONDS]
        
        # Add current request timestamp
        bucket.append(now)
        _rate_limit_store[key] = bucket
        
        # Check if over limit
        if len(bucket) > MAX_REQUESTS:
            return Response(
                content="Too Many Requests",
                status_code=429,
                media_type="text/plain",
            )
        
        # Call the next middleware/handler
        response = await call_next(request)
        return response
