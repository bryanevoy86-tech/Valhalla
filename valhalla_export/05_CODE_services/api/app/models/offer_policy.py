from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, UniqueConstraint
from app.models.base import Base


class OfferPolicy(Base):
    """
    Bounded offer rules by province/market.
    This prevents over-offering when scaling Canada-wide.
    """
    __tablename__ = "offer_policy"
    __table_args__ = (UniqueConstraint("province", "market", name="uq_offer_policy_province_market"),)

    id = Column(Integer, primary_key=True, index=True)
    province = Column(String, nullable=False)
    market = Column(String, nullable=False, default="ALL")

    enabled = Column(Boolean, nullable=False, default=True)

    # Classic wholesaling math knobs
    max_arv_multiplier = Column(Float, nullable=False, default=0.70)  # MAO = ARV * mult - repairs - fees
    default_assignment_fee = Column(Float, nullable=False, default=10000.0)
    default_fees_buffer = Column(Float, nullable=False, default=2500.0)

    changed_by = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
