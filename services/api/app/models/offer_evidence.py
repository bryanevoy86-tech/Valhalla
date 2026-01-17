from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.models.base import Base


class OfferEvidence(Base):
    """
    Evidence trace for an offer calculation (auditable).
    """
    __tablename__ = "offer_evidence"

    id = Column(Integer, primary_key=True, index=True)

    province = Column(String, nullable=False)
    market = Column(String, nullable=False, default="ALL")

    arv = Column(Float, nullable=False)
    repairs = Column(Float, nullable=False)
    fees_buffer = Column(Float, nullable=False)
    mao = Column(Float, nullable=False)
    recommended_offer = Column(Float, nullable=False)

    comps_json = Column(Text, nullable=True)
    assumptions_json = Column(Text, nullable=True)

    correlation_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
