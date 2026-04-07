"""Family OS Models"""
from datetime import datetime
from sqlalchemy import Column, DateTime, JSON, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class FamilyValues(Base):
    """Family mission, core values, and rules."""
    __tablename__ = "family_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission = Column(String, nullable=True)
    core_values = Column(JSON, nullable=True)  # list of strings
    rules = Column(JSON, nullable=True)        # list of {"rule": str, "note": str}
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FamilyRoutine(Base):
    """Family routines (morning, bedtime, etc.)."""
    __tablename__ = "family_routines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False, index=True)  # "Morning", "Bedtime", etc.
    steps = Column(JSON, nullable=True)        # list of {"order": int, "text": str}
    category = Column(String(64), nullable=True)  # morning / evening / weekend
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ScreenTimeRule(Base):
    """Screen time rules by age group."""
    __tablename__ = "screen_time_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    age_group = Column(String(32), nullable=False, index=True)  # "5-8", "9-12", etc.
    max_minutes_per_day = Column(String(16), nullable=False)
    allowed_categories = Column(JSON, nullable=True)  # ["learning", "stories", ...]
    blocked_categories = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
