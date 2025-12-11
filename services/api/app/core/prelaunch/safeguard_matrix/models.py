"""PACK-CORE-PRELAUNCH-01: Safeguard Matrix - Models"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, JSON, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class SafeguardCategory(str, Enum):
    FREEZE = "FREEZE"
    SLOW = "SLOW"
    FAST_TRACK = "FAST_TRACK"


class SafeguardDomain(str, Enum):
    EIA = "EIA"
    ARBITRAGE = "ARBITRAGE"
    BRRRR = "BRRRR"
    CASHFLOW = "CASHFLOW"
    SYSTEM = "SYSTEM"


class SafeguardRule(Base):
    __tablename__ = "safeguard_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    category = Column(SAEnum(SafeguardCategory), nullable=False)
    domain = Column(SAEnum(SafeguardDomain), nullable=False)
    condition_definition = Column(JSON, nullable=True)
    effect_definition = Column(JSON, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
