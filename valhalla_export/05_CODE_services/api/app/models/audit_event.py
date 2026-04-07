# services/api/app/models/audit_event.py

from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    func,
)

from app.core.db import Base


class AuditEvent(Base):
    """
    Audit log events for tracking system changes.
    Maps to the actual audit_logs table in the database.
    """

    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # entity tracking
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)  # Use for filtering by entity (deal_id, lead_id, etc.)
    
    # action tracking
    action = Column(String(100), nullable=True)
    previous_value = Column(String(500), nullable=True)
    new_value = Column(String(500), nullable=True)
    user_id = Column(String(255), nullable=False, default="system")
    notes = Column(Text, nullable=True)
