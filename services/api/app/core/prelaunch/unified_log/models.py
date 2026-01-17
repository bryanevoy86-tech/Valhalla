"""PACK-CORE-PRELAUNCH-01: Unified Log - Models"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, JSON, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class EventType(str, Enum):
    ACTION = "ACTION"
    AUTO = "AUTO"
    RISK = "RISK"
    FINANCE = "FINANCE"
    BRRRR = "BRRRR"
    ARBITRAGE = "ARBITRAGE"
    HOUSEHOLD = "HOUSEHOLD"
    CHILD = "CHILD"
    SYSTEM = "SYSTEM"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class SystemEvent(Base):
    __tablename__ = "system_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_type = Column(SAEnum(EventType), nullable=False)
    source = Column(String(128), nullable=False)
    message = Column(String, nullable=False)
    data = Column(JSON, nullable=True)
    correlation_id = Column(String(64), nullable=True, index=True)
