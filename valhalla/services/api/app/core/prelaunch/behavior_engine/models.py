"""PACK-PRELAUNCH-09: Behavior Engine Models

Human alignment profiling for lawyers, accountants, contractors, partners, and system users.
"""
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, String, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class BehaviorProfile(Base):
    """User behavior profile tracking alignment and risk scores."""
    
    __tablename__ = "behavior_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    role = Column(String(64), nullable=True)  # lawyer, accountant, contractor, partner, etc.
    public_data = Column(JSON, nullable=True)  # Public-facing profile data
    alignment_score = Column(Float, nullable=False)  # 0-100: how aligned with system values
    risk_score = Column(Float, nullable=False)  # 0-100: behavioral risk indicator
    recommended_style = Column(JSON, nullable=True)  # Recommended interaction style

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_behavior_profiles_role", "role"),
        Index("ix_behavior_profiles_created_at", "created_at"),
    )
