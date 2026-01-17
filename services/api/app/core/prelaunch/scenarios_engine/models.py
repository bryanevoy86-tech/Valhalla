"""PACK-CORE-PRELAUNCH-01: Scenarios Engine - Models"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, JSON, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class ScenarioCategory(str, Enum):
    BRRRR = "BRRRR"
    ARBITRAGE = "ARBITRAGE"
    EIA = "EIA"
    FAMILY = "FAMILY"
    SYSTEM = "SYSTEM"
    BRYAN = "BRYAN"


class ScenarioSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(64), unique=True, nullable=False, index=True)
    category = Column(SAEnum(ScenarioCategory), nullable=False)
    severity = Column(SAEnum(ScenarioSeverity), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)

    trigger_conditions = Column(JSON, nullable=True)
    recommended_actions = Column(JSON, nullable=True)
    fallback_actions = Column(JSON, nullable=True)
    auto_actions = Column(JSON, nullable=True)

    enabled = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
