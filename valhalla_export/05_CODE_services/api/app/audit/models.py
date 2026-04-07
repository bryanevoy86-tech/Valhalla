from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from datetime import datetime, timezone
from app.core.db import Base


class AuditEvent(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Entity tracking (generic pattern for deals, leads, offers, etc.)
    entity_type = Column(String, nullable=True)  # "deal", "lead", "offer", etc.
    entity_id = Column(Integer, nullable=True)   # The ID of the entity being audited
    
    # Action and details
    action = Column(String, nullable=True)
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    user_id = Column(String, nullable=False, default="system")
    notes = Column(Text, nullable=True)
