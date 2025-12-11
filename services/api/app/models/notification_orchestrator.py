"""
PACK AG: Notification Orchestrator Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.models.base import Base


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, unique=True)  # email, sms, in_app, push
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, unique=True)  # e.g. "deal_status_update"

    channel_key = Column(String, nullable=False)  # matches NotificationChannel.key

    subject = Column(String, nullable=True)       # email / push title
    body = Column(Text, nullable=False)           # templated body with placeholders like {{deal_id}}

    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)

    channel_key = Column(String, nullable=False)
    template_key = Column(String, nullable=True)

    recipient = Column(String, nullable=False)   # email, phone, user_id, etc.
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=False)

    status = Column(
        String,
        nullable=False,
        default="queued",  # queued, sent, failed
    )
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
