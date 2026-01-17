"""Go-Live State model.

This is a *safety* control-plane model.
It does not redesign Valhalla; it enforces Prime Laws around deployment.
"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, String, DateTime
from app.models.base import Base


class GoLiveState(Base):
    __tablename__ = "go_live_state"

    id = Column(Integer, primary_key=True, index=True, default=1)

    # When False, the API must not allow production-grade execution endpoints.
    go_live_enabled = Column(Boolean, default=False, nullable=False)

    # Emergency stop. When True, execution endpoints are blocked regardless of go_live_enabled.
    kill_switch_engaged = Column(Boolean, default=False, nullable=False)

    # Who/what engaged go-live / kill-switch (human identifier).
    changed_by = Column(String, nullable=True)

    # Human-readable reason / note.
    reason = Column(String, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
