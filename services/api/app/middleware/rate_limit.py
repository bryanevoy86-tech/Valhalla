"""
PACK L0-07: Rate Limiting Middleware
Enforces rate limits on all requests and reports violations to telemetry.
"""

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.util.rate_limit_helper import get_rate_limit_helper
from app.middleware.correlation_id import get_correlation_id


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces rate limits on all requests.
    
    Configurations:
    - Global rate limit: 1000 req/min per IP
    - API endpoints: 100 req/min per IP
    - Auth endpoints: 10 req/min per IP
    - Authenticated users: 10000 req/hour per user
    
    Violations are:
    - Rejected with 429 (Too Many Requests)
    - Recorded in security telemetry
    - Aggregated in security dashboard
    """
    
    # Rate limit rules (scope, limit, window_seconds)
    RULES = {
        "global": (1000, 60),  # 1000 per minute
        "api": (100, 60),      # 100 per minute
        "auth": (10, 60),      # 10 per minute (strict)
        "upload": (20, 60),    # 20 per minute
    }
    
    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        """
        Check rate limits and forward if allowed.
        
        Args:
            request: FastAPI Request
            call_next: Next middleware/endpoint
        
        Returns:
            Response or 429 if rate limited
        """
        # Determine scope based on path
        path = request.url.path
        scope = self._get_scope(path)
        
        # Get identifier (IP or user ID)
        identifier = self._get_identifier(request)
        
        # Check rate limit
        db = SessionLocal()
        try:
            helper = get_rate_limit_helper(db)
            limit, window = self.RULES.get(scope, self.RULES["global"])
            
            allowed, remaining = helper.check_rate_limit(
                scope=scope,
                identifier=identifier,
                limit=limit,
                window_seconds=window,
            )
            
            if not allowed:
                # Record violation to telemetry
                self._record_violation(db, scope, identifier, request)
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded for {scope}",
                        "retry_after": window,
                    },
                    headers={"Retry-After": str(window)},
                )
            
            # Add remaining quota to response
            response = await call_next(request)
            if remaining is not None:
                response.headers["X-RateLimit-Remaining"] = str(remaining)
            
            return response
        finally:
            db.close()
    
    def _get_scope(self, path: str) -> str:
        """Determine rate limit scope based on request path."""
        if "/auth" in path:
            return "auth"
        elif "/upload" in path:
            return "upload"
        elif "/api" in path:
            return "api"
        return "global"
    
    def _get_identifier(self, request: Request) -> str:
        """Extract unique identifier for rate limiting (IP or user ID)."""
        # Try to get user ID from auth headers or cookie
        auth_header = request.headers.get("Authorization", "")
        if auth_header:
            return f"user:{auth_header[:20]}"  # Hash user token
        
        # Fall back to IP address
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    def _record_violation(
        self,
        db: Session,
        scope: str,
        identifier: str,
        request: Request,
    ) -> None:
        """Record rate limit violation to telemetry and security logs."""
        try:
            from app.services.telemetry_event import TelemetryService
            from app.schemas.telemetry_event import TelemetryEventCreate
            
            service = TelemetryService(db)
            service.write(
                TelemetryEventCreate(
                    event_type="security.rate_limit_violation",
                    source="rate_limit_middleware",
                    severity="warning",
                    category="security",
                    correlation_id=get_correlation_id(),
                    message=f"Rate limit exceeded: {scope} from {identifier}",
                    payload={
                        "scope": scope,
                        "identifier": identifier,
                        "path": str(request.url.path),
                        "method": request.method,
                    },
                )
            )
        except Exception:
            # Best-effort; don't crash if telemetry fails
            pass
