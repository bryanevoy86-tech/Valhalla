"""
Lead intake model for tracking raw property leads before normalization.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, func
from ..core.db import Base


class LeadIntake(Base):
    __tablename__ = "lead_intake"
    
    id = Column(Integer, primary_key=True)
    source = Column(String(80), nullable=True)            # "webform","phone","import"
    name = Column(String(160), nullable=True)
    email = Column(String(160), nullable=True)
    phone = Column(String(40), nullable=True)
    address = Column(String(240), nullable=True)
    region = Column(String(120), nullable=True)           # city/area or code
    property_type = Column(String(40), nullable=True)     # SFH, Duplex, etc.
    price = Column(Numeric(18,2), nullable=True)
    beds = Column(Integer, nullable=True)
    baths = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(40), nullable=False, default="new")  # new, normalized, archived
    raw_json = Column(Text, nullable=True)
    deal_id = Column(Integer, nullable=True)              # created DealBrief id (if any)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
