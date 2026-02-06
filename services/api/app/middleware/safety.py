"""
Module 44: Runtime Safety Guard
Middleware that prevents operations when system is disabled.
"""
from fastapi import Request
from app.system.kill_switch import is_enabled


async def safety_guard(request: Request, call_next):
    """
    Safety middleware that checks if system is enabled.
    If disabled, returns error for all requests except health checks.
    
    Args:
        request: Incoming request
        call_next: Next middleware/handler
    
    Returns:
        Response or error
    """
    # Allow health checks and admin endpoints even when disabled
    allow_disabled_paths = [
        "/health",
        "/api/system/state",
        "/admin/status",
        "/webhooks"  # Still receive webhooks
    ]
    
    path = request.url.path
    
    # Check if this path is allowed when system is disabled
    is_allowed = any(path.startswith(p) for p in allow_disabled_paths)
    
    if not is_enabled() and not is_allowed:
        return {
            "error": "system_disabled",
            "message": "System is currently disabled. Contact administrator.",
            "status": 503
        }
    
    response = await call_next(request)
    return response
