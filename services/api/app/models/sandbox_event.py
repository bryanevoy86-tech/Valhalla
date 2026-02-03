"""Sandbox event log for activity tracking."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.db import Base


class SandboxEvent(Base):
    __tablename__ = "sandbox_events"

    id = Column(Integer, primary_key=True)
    engine_name = Column(String(64), nullable=False)
    event_type = Column(String(64), nullable=False)     # e.g. OUTREACH_BLOCKED_QUEUED
    payload_json = Column(Text, nullable=True)          # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
