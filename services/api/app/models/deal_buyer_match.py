"""
Deal-to-buyer match model for tracking buyer associations with deals.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, func, ForeignKey
from ..core.db import Base


class DealBuyerMatch(Base):
    __tablename__ = "deal_buyer_matches"
    
    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, nullable=False)  # FK to deal_briefs (not enforced for flexibility)
    buyer_id = Column(Integer, ForeignKey("buyer_candidates.id"), nullable=False)
    match_strength = Column(Float, nullable=True, default=0.0)
    identified_date = Column(DateTime(timezone=True), nullable=True)
    match_status = Column(String(20), nullable=False, default="candidate")  # candidate, contacted, interested, passed, assigned
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __init__(self, **kwargs):
        if kwargs.get("identified_date") is not None and kwargs.get("created_at") is None:
            kwargs["created_at"] = kwargs.get("identified_date")

        if kwargs.get("match_status") is None and kwargs.get("status") is not None:
            kwargs["match_status"] = kwargs.get("status")

        super().__init__(**kwargs)
