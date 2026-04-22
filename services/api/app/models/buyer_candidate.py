"""
Buyer candidate model for simple buyer management.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from ..core.db import Base


class BuyerCandidate(Base):
    __tablename__ = "buyer_candidates"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(160), nullable=False)
    email = Column(String(160), nullable=True)
    phone = Column(String(20), nullable=True)
    buy_box = Column(Text, nullable=True)  # JSON string describing buying criteria
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
