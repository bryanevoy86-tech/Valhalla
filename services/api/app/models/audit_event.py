# services/api/app/models/audit_event.py

from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    func,
)

from app.core.db import Base


class AuditEvent(Base):
    """
    Operational audit events for tracking compliance and process issues.
    Not legal advice - pure operational rule-based logging.
    """

    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)

    deal_id = Column(Integer, nullable=True)
    professional_id = Column(Integer, nullable=True)

    code = Column(String(100), nullable=False)  # e.g. "MISSING_SIGNED_CONTRACT"
    severity = Column(String(50), default="warning")  # info, warning, critical
    message = Column(String(500), nullable=False)

    is_resolved = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
