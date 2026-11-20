"""Central API authorization dependencies.

Server credentials must never silently turn a production write endpoint into
an anonymous endpoint merely because a configuration variable was omitted.
"""
from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException, status

from .settings import settings


def require_builder_key(x_api_key: str | None = Header(None, alias="X-API-Key")) -> bool:
    if not settings.BUILDER_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Builder key not configured",
        )
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.BUILDER_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-API-Key",
        )
    return True


def require_auth(
    x_session_token: str | None = Header(None, alias="X-Session-Token"),
) -> bool:
    """Guard legacy session-token endpoints.

    Explicit developer-only anonymous mode requires BOTH env=dev and
    VALHALLA_ALLOW_UNAUTH_DEV=true. The default is always fail-closed.
    """
    expected = settings.SESSION_TOKEN_DEV
    if not expected:
        developer_override = (
            settings.env.strip().lower() == "dev"
            and os.environ.get("VALHALLA_ALLOW_UNAUTH_DEV", "").strip().lower()
            in {"1", "true", "yes"}
        )
        if developer_override:
            return True
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session-token authorization not configured",
        )
    if not x_session_token or not hmac.compare_digest(x_session_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: X-Session-Token required",
        )
    return True
