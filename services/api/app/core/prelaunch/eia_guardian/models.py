"""PACK-PRELAUNCH-10: EIA Guardian Engine Models

Ensures you DO NOT accidentally break EIA rules before the system is profitable.
"""
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, String, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class EIAStatus(Base):
    """EIA (Earned Income Averaging) status and risk tracking."""
    
    __tablename__ = "eia_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    monthly_limit = Column(Float, nullable=False)  # Monthly income limit for EIA compliance
    current_income = Column(Float, nullable=False)  # Current month's income
    projected_income = Column(Float, nullable=False)  # Projected month's income
    risk_level = Column(String(32), nullable=False)  # RED, YELLOW, GREEN
    recommendations = Column(JSON, nullable=True)  # Recommended actions

    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_eia_status_updated_at", "updated_at"),
    )
