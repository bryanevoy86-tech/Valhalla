from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.db import Base


class ProviderToken(Base):
    __tablename__ = "provider_tokens"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    provider = Column(String(32), nullable=False)
    account_ref = Column(String(128))
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expires_at = Column(DateTime)
    scopes = Column(Text)


class ProviderWebhookEvent(Base):
    __tablename__ = "provider_webhook_events"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    provider = Column(String(32), nullable=False)
    event_type = Column(String(128), nullable=False)
    payload = Column(Text, nullable=False)
    signature = Column(String(256))
    processed = Column(Boolean, nullable=False, server_default="0")
    error_msg = Column(Text)
