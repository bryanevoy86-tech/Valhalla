"""Persistent WeWeb access-token revocation records.

Only irreversible SHA-256 hashes of random JWT jti values are stored, never
the actual bearer token. Shared PostgreSQL makes revocation survive restarts.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String
from app.models.base import Base


class RevokedAccessToken(Base):
    __tablename__ = "auth_revoked_access_tokens"

    id = Column(Integer, primary_key=True)
    jti_sha256 = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
