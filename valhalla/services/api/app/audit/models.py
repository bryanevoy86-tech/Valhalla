from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime, timezone
from app.core.db import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String, nullable=False)  # user id/email/bot
    action = Column(String, nullable=False)  # e.g., "deal.create"
    target = Column(String, nullable=True)  # e.g., deal:123
    result = Column(String, nullable=False)  # "success" | "failure"
    ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)  # arbitrary details
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
