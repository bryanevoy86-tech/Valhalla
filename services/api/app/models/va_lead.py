"""
VA Lead model - Virtual Assistant intake leads with Heimdall scoring.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, Float, func
from ..core.db import Base


class VALead(Base):
    __tablename__ = "va_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Source information
    source_platform = Column(String(60), nullable=False)  # facebook, kijiji, google_maps, etc.
    source_type = Column(String(60), nullable=False)       # manual_va, manual_owner, public_listing, etc.
    source_url = Column(String(500), nullable=True)
    
    # Property information
    address = Column(String(240), nullable=True)
    city = Column(String(120), nullable=True)
    province = Column(String(10), nullable=True)
    
    # Seller information
    seller_name = Column(String(160), nullable=True)
    seller_phone = Column(String(40), nullable=True)
    seller_email = Column(String(160), nullable=True)
    
    # Property details
    asking_price = Column(Numeric(15, 2), nullable=True)
    
    # Raw input and notes
    raw_text = Column(Text, nullable=True)
    va_notes = Column(Text, nullable=True)
    
    # Strategy
    strategy_fit = Column(String(60), nullable=True)  # wholesale, brrr, flip, rental, unknown
    submitted_by = Column(String(80), nullable=False, default="va")
    
    # Heimdall scoring
    heimdall_score = Column(Integer, nullable=False, default=0)
    risk_level = Column(String(20), nullable=False, default="high")  # low, medium, high
    confidence = Column(Float, nullable=False, default=0.0)
    recommended_action = Column(String(255), nullable=True)
    
    # Pipeline
    status = Column(String(60), nullable=False, default="pending")  # pending, qualified_pending_approval, research_required, parked, approved, converted, rejected
    stage = Column(String(60), nullable=False, default="intake")    # intake, research, approval_required, approved, deal_conversion, converted, archived
    
    # Deal linkage
    deal_id = Column(Integer, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
