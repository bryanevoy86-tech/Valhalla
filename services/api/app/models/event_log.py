"""
PACK AH: Event Log / Timeline Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.models.base import Base


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)

    # generic "what this is about"
    entity_type = Column(String, nullable=False)  # deal, property, child, professional, etc.
    entity_id = Column(String, nullable=True)     # keep as string to support composite ids

    event_type = Column(String, nullable=False)   # deal_status_changed, audit_created, etc.
    source = Column(String, nullable=True)        # system, heimdall, user, va, worker, etc.

    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
