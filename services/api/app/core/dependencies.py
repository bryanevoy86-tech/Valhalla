from fastapi import Depends, Header, HTTPException, status
from .settings import settings

def require_builder_key(x_api_key: str = Header(None, alias="X-API-Key")):
    if not settings.HEIMDALL_BUILDER_API_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Builder key not configured")
    if not x_api_key or x_api_key != settings.HEIMDALL_BUILDER_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid X-API-Key")
    return True
