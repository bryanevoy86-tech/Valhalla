"""
Lead models for Advanced Lead Scraper (Pack 31).

Actual persistent schema (valhalla_local.db):
- lead_name, lead_email, lead_phone (seller/contact)
- property_address, property_city, property_state, property_zip (location)
- estimated_arv (after-repair value)
- lead_status, source, notes
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text
from app.core.db import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    
    # Contact information
    lead_name = Column(String(255), nullable=False)
    lead_email = Column(String(255), nullable=False, index=True)
    lead_phone = Column(String(20), nullable=False)
    
    # Property location
    property_address = Column(String(512), nullable=True)
    property_city = Column(String(255), nullable=True)
    property_state = Column(String(2), nullable=True)
    property_zip = Column(String(10), nullable=True)
    
    # Valuation
    estimated_arv = Column(Numeric(15, 2), nullable=True)
    
    # Status & source
    lead_status = Column(String(50), default="new", nullable=False)  # new, contacted, qualified, disqualified
    source = Column(String(255), nullable=False)  # e.g., Zillow, MLS, API, partner, direct
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_ts = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_ts = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
