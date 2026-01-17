"""
PACK AX: Feature Flags & Experiments Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.models.base import Base


class FeatureFlag(Base):
    """Feature flags and A/B experiment variants for safe feature rollout."""
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)

    key = Column(String, nullable=False, unique=True)   # e.g. "kids_story_mode"
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    enabled = Column(Boolean, default=False)

    audience = Column(String, nullable=True)            # global, kids, family, founders, ops
    variant = Column(String, nullable=True)             # A, B, test1, etc.

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
