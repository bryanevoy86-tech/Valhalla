from __future__ import annotations

from fastapi import Request
from ..security.models import Identity

def get_identity(request: Request) -> Identity:
    """
    DEV/STUB identity:
    - If you pass X-USER-ID / X-USER-EMAIL / X-SCOPES headers, it uses them.
    - Otherwise defaults to owner (for local dev).
    Later you swap this to real auth (JWT, session, etc.).
    """
    user_id = request.headers.get("X-USER-ID", "dev-owner")
    email = request.headers.get("X-USER-EMAIL", "dev@valhalla.local")

    scopes_raw = request.headers.get("X-SCOPES", "owner")
    scopes = [s.strip() for s in scopes_raw.split(",") if s.strip()]

    # allow forcing inactive subscription for testing
    sub_raw = request.headers.get("X-SUB-ACTIVE", "true").lower()
    is_active = sub_raw not in ("0", "false", "no")

    return Identity(
        user_id=user_id,
        email=email,
        scopes=scopes,
        is_active_subscription=is_active,
    )
