from fastapi import Depends, Header, HTTPException, status
from .settings import settings

def require_builder_key(x_api_key: str = Header(None, alias="X-API-Key")):
    if not settings.BUILDER_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Builder key not configured")
    if not x_api_key or x_api_key != settings.BUILDER_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid X-API-Key")
    return True


def require_auth(x_session_token: str = Header(None, alias="X-Session-Token")) -> bool:
    """
    Lightweight session-based auth for write operations.
    
    Checks for X-Session-Token header matching configured SESSION_TOKEN_DEV.
    If no session token is configured, auth is skipped (dev mode).
    
    Args:
        x_session_token: Session token from request header
    
    Returns:
        True if authenticated
    
    Raises:
        HTTPException: 401 if token required but invalid/missing
    """
    # If no session token is configured, skip auth (dev mode)
    if not settings.SESSION_TOKEN_DEV:
        return True
    
    # Session token is configured, so it's required
    if not x_session_token or x_session_token != settings.SESSION_TOKEN_DEV:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: X-Session-Token required"
        )
    
    return True
