"""
Outbox model for queuing notifications (webhooks, emails) for async dispatch.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from ..core.db import Base


class Outbox(Base):
    __tablename__ = "outbox"
    
    id = Column(Integer, primary_key=True)
    kind = Column(String(20), nullable=False)            # "webhook","email"
    target = Column(String(240), nullable=True)          # URL or email
    subject = Column(String(240), nullable=True)         # for email
    payload_json = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="queued")  # queued, sent, error
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
