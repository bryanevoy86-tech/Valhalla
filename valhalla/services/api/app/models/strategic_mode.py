"""
PACK CI7: Strategic Mode Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from app.models.base import Base


class StrategicMode(Base):
    """
    A named mode that changes how the system behaves.
    Example: 'growth', 'war', 'recovery', 'family_focus'.
    """
    __tablename__ = "strategic_modes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Optional: default tuning profile linked by name
    tuning_profile_name = Column(String, nullable=True)

    # Optional: mode-specific weights/overrides
    parameters = Column(JSON, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ActiveMode(Base):
    """
    Current active mode (there should generally be 1 row).
    """
    __tablename__ = "active_modes"

    id = Column(Integer, primary_key=True, index=True, default=1)
    mode_name = Column(String, nullable=False)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(Text, nullable=True)
