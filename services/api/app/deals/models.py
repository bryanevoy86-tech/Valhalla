"""
Deal models for the core deal pipeline.

Persistent SQLAlchemy models for deals that track through the full lifecycle:
lead_received -> intake_review -> underwrite_ready -> offer_ready -> offer_sent -> 
contract_pending -> contract_signed -> buyer_matching -> dispo_ready -> closed -> dead
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey, Enum
from app.core.db import Base
import enum


class DealStage(str, enum.Enum):
    """Deal stages through the pipeline lifecycle."""
    lead_received = "lead_received"
    intake_review = "intake_review"
    underwrite_ready = "underwrite_ready"
    offer_ready = "offer_ready"
    offer_sent = "offer_sent"
    contract_pending = "contract_pending"
    contract_signed = "contract_signed"
    buyer_matching = "buyer_matching"
    dispo_ready = "dispo_ready"
    closed = "closed"
    dead = "dead"


class DealStatus(str, enum.Enum):
    """Overall deal status."""
    active = "active"
    on_hold = "on_hold"
    archived = "archived"


class Deal(Base):
    """
    Deal entity tracking a real estate opportunity from lead to close.
    
    Fields connect the deal to leads and offers, track valuation,
    stage progression, and disposition outcome.
    """
    __tablename__ = "deals"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Foreign keys & relationships
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Deal identity & classification
    title = Column(String(255), nullable=False)
    stage = Column(String(50), nullable=False, default="lead_received", index=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    
    # Valuation metrics
    arv = Column(Numeric(15, 2), nullable=True)  # After-Repair Value
    estimated_repair_cost = Column(Numeric(15, 2), nullable=True)
    max_allowable_offer = Column(Numeric(15, 2), nullable=True)
    target_assignment_fee = Column(Numeric(15, 2), nullable=True)
    
    # Scoring & analysis
    score = Column(Numeric(8, 2), nullable=True, default=0)
    
    # Notes & disposition
    notes = Column(Text, nullable=True)
    disposition_status = Column(String(50), nullable=True)  # matched, pending, expired, etc.
    
    def __repr__(self) -> str:
        return f"<Deal(id={self.id}, title={self.title}, stage={self.stage}, lead_id={self.lead_id})>"
