"""
Audit log model for tracking deal events.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from ..core.db import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, nullable=True)  # Can be null for non-deal events
    event_type = Column(String(60), nullable=False)  # e.g., "deal_created", "deal_analyzed", "disposition_updated"
    event_source = Column(String(20), nullable=False, default="system")  # "system" or "user"
    message = Column(String(500), nullable=False)
    event_data = Column(Text, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
