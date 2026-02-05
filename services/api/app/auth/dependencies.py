from __future__ import annotations

import os
from fastapi import Header, HTTPException, status

API_KEY_HEADER = "X-API-Key"
ENV_KEY_NAME = "VALHALLA_API_KEY"

def require_api_key(x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER)) -> str:
    """
    Minimal dependency used by routers that expect app.auth.dependencies.

    Looks for:
      - request header: X-API-Key
      - env var: VALHALLA_API_KEY
    """
    expected = os.getenv(ENV_KEY_NAME)
    if not expected:
        # In dev, you can allow missing key to avoid blocking local testing.
        # But in prod you should set VALHALLA_API_KEY.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{ENV_KEY_NAME} is not set",
        )

    if not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return x_api_key


def get_current_admin_user(api_key: str = Header(default=None, alias="X-API-Key")) -> str:
    """
    Admin user dependency used by security, optimization, telemetry, diagnostics routers.
    
    Validates API key and returns the authenticated user identifier.
    """
    return require_api_key(api_key)
