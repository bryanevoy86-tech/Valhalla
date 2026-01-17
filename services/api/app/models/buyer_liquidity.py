from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, UniqueConstraint
from app.models.base import Base


class BuyerLiquidityNode(Base):
    """
    Aggregated buyer depth per (province, market, property_type).
    """
    __tablename__ = "buyer_liquidity_node"
    __table_args__ = (UniqueConstraint("province", "market", "property_type", name="uq_liq_node"),)

    id = Column(Integer, primary_key=True, index=True)
    province = Column(String, nullable=False)
    market = Column(String, nullable=False, default="ALL")
    property_type = Column(String, nullable=False, default="SFR")  # SFR, MF, LAND, COMMERCIAL, etc.

    buyer_count = Column(Integer, nullable=False, default=0)
    active_buyer_count = Column(Integer, nullable=False, default=0)
    avg_response_rate = Column(Float, nullable=False, default=0.0)
    avg_close_rate = Column(Float, nullable=False, default=0.0)

    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class BuyerFeedbackEvent(Base):
    """
    Feedback loop from dispositions:
    - buyer responded / no response
    - buyer bought / passed
    """
    __tablename__ = "buyer_feedback_event"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(String, nullable=True)
    province = Column(String, nullable=False)
    market = Column(String, nullable=False, default="ALL")
    property_type = Column(String, nullable=False, default="SFR")

    event = Column(String, nullable=False)  # "RESPONDED"|"NO_RESPONSE"|"BOUGHT"|"PASSED"
    correlation_id = Column(String, nullable=True)
    detail = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
