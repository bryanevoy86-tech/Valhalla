"""
Deal notification model for recording deal events.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func
from ..core.db import Base


class DealNotification(Base):
    __tablename__ = "deal_notifications"
    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, ForeignKey("deal_briefs.id"), nullable=True)
    type = Column(String(60), nullable=False)  # analysis_complete, moved_to_pipeline, marked_dead, disposition_updated
    title = Column(String(240), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
