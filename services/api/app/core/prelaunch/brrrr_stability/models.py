"""PACK-PRELAUNCH-12: BRRRR Stability Engine Models

Gives Heimdall real-time ability to evaluate which BRRRR properties are stable,
which need intervention, which are unsafe to refi, and which zones are ready for expansion.
"""
from datetime import datetime
from sqlalchemy import Column, Float, JSON, DateTime, String, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class BRRRRStability(Base):
    """BRRRR property stability tracking and evaluation."""
    
    __tablename__ = "brrrr_stability"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_address = Column(String(255), nullable=False)
    stability_score = Column(Float, nullable=False)  # 0-100 stability rating
    risk_factors = Column(JSON, nullable=True)  # Identified risk factors
    recommendations = Column(JSON, nullable=True)  # Recommended actions (refi, hold, exit, expand)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_brrrr_stability_updated_at", "updated_at"),
        Index("ix_brrrr_stability_property_address", "property_address"),
    )
