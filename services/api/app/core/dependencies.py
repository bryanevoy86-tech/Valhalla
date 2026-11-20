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
    if not x_api_key or not hmac.compare_digest(x_api_key.encode("utf-8"), settings.BUILDER_KEY.encode("utf-8")):
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
    if not x_session_token or not hmac.compare_digest(x_session_token.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: X-Session-Token required",
        )
    return True


def require_prime_control_key(
    x_prime_control_key: str | None = Header(None, alias="X-Prime-Control-Key"),
) -> bool:
    """Private server-to-server control plane; never share with SaaS tenants.
    
    Deliberately independent of the Builder and Business Factory keys.
    """
    expected = os.environ.get("VALHALLA_PRIME_CONTROL_KEY", "")
    other_keys = {settings.BUILDER_KEY, settings.SESSION_TOKEN_DEV,
                  settings.jwt_secret, os.environ.get("VALHALLA_FACTORY_KEY"),
                  os.environ.get("VALHALLA_OWNER_MANDATE_KEY")}
    if not expected or expected in other_keys:
        raise HTTPException(status_code=503, detail="Distinct Prime control key not configured")
    if not x_prime_control_key or not hmac.compare_digest(
        x_prime_control_key.encode("utf-8"), expected.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Prime control authentication required")
    return True
