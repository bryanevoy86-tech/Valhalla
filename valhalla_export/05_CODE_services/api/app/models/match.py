"""
Buyer matching models for deal-to-buyer intelligence.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric, func
from ..core.db import Base

class Buyer(Base):
    __tablename__ = "buyers"
    id = Column(Integer, primary_key=True)
    name = Column(String(160), nullable=False)
    email = Column(String(160), nullable=True)
    phone = Column(String(40), nullable=True)
    regions = Column(String(240), nullable=True)        # comma list e.g., "Winnipeg,Brandon,CA-MB"
    property_types = Column(String(160), nullable=True) # "SFH,Duplex,Triplex"
    min_price = Column(Numeric(18,2), nullable=True)
    max_price = Column(Numeric(18,2), nullable=True)
    min_beds = Column(Integer, nullable=True)
    min_baths = Column(Integer, nullable=True)
    tags = Column(String(240), nullable=True)           # freeform labels
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class DealBrief(Base):
    __tablename__ = "deal_briefs"
    id = Column(Integer, primary_key=True)
    headline = Column(String(240), nullable=False)      # e.g., "SFH in Transcona, solid bones"
    region = Column(String(120), nullable=True)         # city/area or code
    property_type = Column(String(40), nullable=True)   # "SFH","Duplex",...
    price = Column(Numeric(18,2), nullable=True)
    beds = Column(Integer, nullable=True)
    baths = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(40), nullable=False, default="active")  # active, under_contract, sold, archived
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
