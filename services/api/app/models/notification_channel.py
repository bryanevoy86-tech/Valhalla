"""
PACK UG: Notification & Alert Channel Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from app.models.base import Base


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    channel_type = Column(String, nullable=False)
    target = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    channel_id = Column(Integer, nullable=False)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="pending")
    last_error = Column(Text, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
