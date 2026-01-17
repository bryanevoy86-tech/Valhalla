"""
PACK CI5: Heimdall Tuning Ruleset Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from app.models.base import Base


class TuningProfile(Base):
    """
    Named tuning profile for Heimdall's advisory style.
    Example: 'default', 'war_mode', 'family_protect', etc.
    """
    __tablename__ = "tuning_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Core sliders (0-100)
    aggression = Column(Integer, nullable=False, default=50)
    risk_tolerance = Column(Integer, nullable=False, default=50)
    safety_bias = Column(Integer, nullable=False, default=70)
    growth_bias = Column(Integer, nullable=False, default=70)
    stability_bias = Column(Integer, nullable=False, default=60)

    # JSON for extra weights (per domain, etc.)
    weights = Column(JSON, nullable=True)

    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class TuningConstraint(Base):
    """
    Hard constraints/guardrails Heimdall must respect.
    Example:
    - 'no illegal actions'
    - 'avoid custody risk moves'
    - 'never exceed X% bankroll'
    """
    __tablename__ = "tuning_constraints"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, nullable=False, index=True)
    key = Column(String, nullable=False)          # e.g. "custody_risk", "legal_compliance"
    description = Column(Text, nullable=False)
    rules = Column(JSON, nullable=True)           # structured conditions
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
