"""
PACK AJ: Timeline → Notification Bridge Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.models.base import Base


class NotificationPreference(Base):
    """
    Per-user preferences for which event types they want notification on.
    """
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)      # user in your auth system
    entity_type = Column(String, nullable=True)    # deal, property, child, etc. (optional filter)
    event_type = Column(String, nullable=False)    # e.g. deal_status_changed

    channel_key = Column(String, nullable=False)   # email, sms, in_app, etc.
    template_key = Column(String, nullable=False)  # key in NotificationTemplate

    is_enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
