"""
Offer models for the core deal pipeline.

Persistent SQLAlchemy models for purchase offers on deals.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey
from app.core.db import Base


class Offer(Base):
    """
    Offer entity representing a purchase offer on a deal.
    
    Tracks the offer price, terms, and status through generation,
    sending, acceptance, and contract generation.
    """
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Foreign keys
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False, index=True)
    
    # Offer terms
    offer_price = Column(Numeric(15, 2), nullable=False)
    emd_amount = Column(Numeric(15, 2), nullable=True)  # Earnest Money Deposit
    closing_window_days = Column(Integer, nullable=True)
    conditions_summary = Column(Text, nullable=True)
    
    # Metadata
    generated_by = Column(String(255), nullable=True)  # System or user email
    status = Column(String(50), nullable=False, default="draft", index=True)
    # draft, sent, accepted, rejected, expired

    def __repr__(self) -> str:
        return f"<Offer(id={self.id}, deal_id={self.deal_id}, offer_price={self.offer_price}, status={self.status})>"
