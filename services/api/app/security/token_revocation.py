"""Durable JWT revocation: never substitute a process-local cache.

The signing/expiry check happens separately. This layer requires a real
database transaction and a known, expiring, uniquely identified access token.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.auth_revocations import RevokedAccessToken


def _validate_payload(payload: dict[str, Any]) -> tuple[str, int, int]:
    jti = payload.get("jti")
    expiry = payload.get("exp")
    user_id = payload.get("user_id")
    if not isinstance(jti, str) or not 1 <= len(jti) <= 256:
        raise ValueError("Missing or invalid JWT token identifier")
    if isinstance(expiry, bool) or not isinstance(expiry, int) or expiry <= 0:
        raise ValueError("Missing or invalid JWT expiry")
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Missing or invalid user identity")
    return hashlib.sha256(jti.encode("utf-8")).hexdigest(), expiry, user_id


def is_access_token_revoked(db: Session, payload: dict[str, Any]) -> bool:
    hashed, _, _ = _validate_payload(payload)
    return (
        db.query(RevokedAccessToken)
        .filter(RevokedAccessToken.jti_sha256 == hashed)
        .first()
        is not None
    )


def revoke_access_token(db: Session, payload: dict[str, Any]) -> bool:
    """Write revocation in caller transaction; caller must commit before success."""
    hashed, expiry, user_id = _validate_payload(payload)
    existing = db.query(RevokedAccessToken).filter_by(jti_sha256=hashed).first()
    if existing:
        return False
    db.add(RevokedAccessToken(
        jti_sha256=hashed,
        user_id=user_id,
        expires_at=datetime.fromtimestamp(expiry, tz=timezone.utc),
    ))
    db.flush()
    return True
