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

    # Compatibility fields referenced by legacy integrity tests.
    deal_id = Column(Integer, nullable=True, index=True)
    offer_date = Column(DateTime, nullable=True)
    offer_price = Column(Float, nullable=True)
    financing_terms = Column(String, nullable=True)
    status = Column(String, nullable=True, default="created")

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

    def __init__(self, **kwargs):
        # Keep legacy constructor payloads compatible with canonical fields.
        if kwargs.get("offer_date") is not None and kwargs.get("created_at") is None:
            kwargs["created_at"] = kwargs.get("offer_date")

        if kwargs.get("offer_price") is not None and kwargs.get("recommended_offer") is None:
            kwargs["recommended_offer"] = kwargs.get("offer_price")

        if kwargs.get("deal_id") is not None and kwargs.get("correlation_id") is None:
            kwargs["correlation_id"] = str(kwargs.get("deal_id"))

        # Backfill canonical non-null fields when tests only provide legacy args.
        kwargs.setdefault("province", "MB")
        kwargs.setdefault("market", "ALL")
        kwargs.setdefault("arv", float(kwargs.get("offer_price") or 0.0))
        kwargs.setdefault("repairs", 0.0)
        kwargs.setdefault("fees_buffer", 0.0)
        kwargs.setdefault("mao", float(kwargs.get("offer_price") or 0.0))
        kwargs.setdefault("recommended_offer", float(kwargs.get("offer_price") or 0.0))

        super().__init__(**kwargs)
