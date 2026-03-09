"""Pending actions / approvals model for SANDBOX visibility."""
from __future__ import annotations

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.db import Base


class PendingActionStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class PendingAction(Base):
    __tablename__ = "pending_actions"

    id = Column(Integer, primary_key=True)
    engine_name = Column(String(64), nullable=False)
    action_type = Column(String(64), nullable=False)      # e.g. OUTREACH_EMAIL
    status = Column(String(16), nullable=False, default=PendingActionStatus.PENDING.value)

    # Who/what it would affect
    target = Column(String(240), nullable=True)           # email, url, etc
    subject = Column(String(240), nullable=True)

    # Human-visible preview + machine payload
    preview_text = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True)

    # Metadata / trace
    reason = Column(Text, nullable=True)                  # why it was queued (engine gate message)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
