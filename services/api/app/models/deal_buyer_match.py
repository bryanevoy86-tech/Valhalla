"""
Deal-to-buyer match model for tracking buyer associations with deals.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey
from ..core.db import Base


class DealBuyerMatch(Base):
    __tablename__ = "deal_buyer_matches"
    
    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, nullable=False)  # FK to deal_briefs (not enforced for flexibility)
    buyer_id = Column(Integer, ForeignKey("buyer_candidates.id"), nullable=False)
    match_status = Column(String(20), nullable=False, default="candidate")  # candidate, contacted, interested, passed, assigned
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
