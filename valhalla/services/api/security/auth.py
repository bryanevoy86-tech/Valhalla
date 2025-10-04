import os
from fastapi import Header, HTTPException

def require_api_key(authorization: str = Header(None)):
    expected = f"Bearer {os.environ['WEWEB_SHARED_SECRET']}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
