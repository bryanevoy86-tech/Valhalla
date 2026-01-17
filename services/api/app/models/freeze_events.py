"""
Freeze Events Model - Tracks deal freeze events and closing milestones
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.models.base import Base


class FreezeEvent(Base):
    """Tracks freeze events, closing dates, and deal milestone events."""
    __tablename__ = "freeze_events"

    id = Column(Integer, primary_key=True, index=True)

    deal_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False)  # freeze, closing, milestone, etc.
    event_name = Column(String, nullable=True)
    
    scheduled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    notes = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
