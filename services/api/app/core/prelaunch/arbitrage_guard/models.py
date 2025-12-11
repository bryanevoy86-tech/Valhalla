"""PACK-PRELAUNCH-11: Arbitrage Guard Engine Models

Protects your bankroll and automatically switches between SAFE / NORMAL / AGGRESSIVE.
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class ArbitrageSettings(Base):
    """Arbitrage trading mode and risk settings."""
    
    __tablename__ = "arbitrage_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mode = Column(String(32), default="SAFE", nullable=False)  # SAFE, NORMAL, AGGRESSIVE
    bankroll = Column(Float, nullable=False)  # Total bankroll available
    max_daily_risk = Column(Float, nullable=False)  # Max daily loss tolerance
    max_monthly_risk = Column(Float, nullable=False)  # Max monthly loss tolerance
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_arbitrage_settings_updated_at", "updated_at"),
    )
