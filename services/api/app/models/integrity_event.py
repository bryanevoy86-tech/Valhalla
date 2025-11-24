from sqlalchemy import Column, Integer, String, DateTime, Text
import datetime
from app.core.db import Base


class IntegrityEvent(Base):
    __tablename__ = "integrity_events"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)  # Heimdall, API, Worker, User
    category = Column(String, nullable=False)  # deal, trust, vault, shield, etc.
    action = Column(String, nullable=False)  # created, updated, flagged, etc.
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    severity = Column(String, default="info")  # info / warn / critical
    message = Column(String, nullable=False)
    payload = Column(Text)  # optional JSON/text dump
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


__all__ = ["IntegrityEvent"]
