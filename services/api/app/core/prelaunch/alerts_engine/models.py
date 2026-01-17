"""PACK-CORE-PRELAUNCH-01: Alerts Engine - Models"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, JSON, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class AlertLevel(str, Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class AlertDomain(str, Enum):
    FINANCE = "FINANCE"
    BRRRR = "BRRRR"
    ARBITRAGE = "ARBITRAGE"
    HOUSEHOLD = "HOUSEHOLD"
    EIA = "EIA"
    SYSTEM = "SYSTEM"
    OTHER = "OTHER"


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(SAEnum(AlertLevel), nullable=False)
    domain = Column(SAEnum(AlertDomain), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(String, nullable=False)
    alert_metadata = Column(JSON, nullable=True)
    status = Column(SAEnum(AlertStatus), default=AlertStatus.OPEN, nullable=False)
    source = Column(String(128), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
