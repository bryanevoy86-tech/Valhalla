"""PACK 76: Global Trust Matrix + Shield / Black Ice Protection Stack
Legal structures, asset protections, and emergency operating modes.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text

from app.models.base import Base


class TrustEntity(Base):
    __tablename__ = "trust_entity"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    jurisdiction = Column(String, nullable=False)
    role = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ShieldMode(Base):
    __tablename__ = "shield_mode"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String, nullable=False)
    active = Column(Boolean, default=False)
    trigger_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
