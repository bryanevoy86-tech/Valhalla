"""
Normalized Lead model - standardized lead records after ingestion and normalization.

This is the operational lead record that scoring, routing, and operators work with.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class NormalizedLead(Base):
    """
    Standardized lead record in Valhalla format.
    
    Fields:
        id: Unique identifier
        source_id: Which lead source this originated from
        external_id: ID assigned by the source system
        full_name: Operator or contact name
        company_name: Company/property name
        phone: Contact phone
        email: Contact email
        address: Full address
        city: City
        market: Market/geography tag
        lead_type: Type of lead (wholesaler, buyer, property, etc.)
        asking_price: Price if applicable
        tags: JSON array of categorization tags
        score: Lead quality score (0-100)
        status: Current status (new, review, contacted, assigned, closed, etc.)
        assigned_to: Operator assigned to this lead
        duplicate_of: If merged/marked duplicate, reference original
        created_at: When normalized
        updated_at: Last modification
    """
    
    __tablename__ = "normalized_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("lead_sources.id"), nullable=False, index=True)
    external_id = Column(String(255), nullable=True, index=True)
    
    # Contact information
    full_name = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    
    # Address and market
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    market = Column(String(100), nullable=True, index=True)
    
    # Lead specifics
    lead_type = Column(String(50), nullable=True)  # wholesaler, buyer, property, etc.
    asking_price = Column(Float, nullable=True)
    
    # Operational fields
    tags = Column(JSON, default=list)  # Array of tags
    score = Column(Float, default=0.0)  # 0-100
    status = Column(String(20), default="new")  # new, review, contacted, assigned, closed, etc.
    assigned_to = Column(String(255), nullable=True)  # Operator username
    duplicate_of = Column(Integer, nullable=True)  # If merged, original lead ID
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    source = relationship("LeadSource", back_populates="normalized_leads")
    
    def __repr__(self):
        return f"<NormalizedLead(id={self.id}, company={self.company_name}, source_id={self.source_id})>"
