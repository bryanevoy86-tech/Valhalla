"""
Lead Source model for the lead acquisition engine.

Tracks external sources of leads (websites, APIs, databases, etc.)
and manages ingestion scheduling and monitoring.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship

from app.core.db import Base


class LeadSource(Base):
    """
    Represents an external source of leads.
    
    Fields:
        id: Unique identifier
        name: Display name of the source
        source_type: Type (api, scraper, csv, webhook, etc.)
        sector: Business sector (wholesaling, real_estate, etc.)
        base_url: Base URL for API or web scraping
        active: Whether this source is currently active
        scrape_frequency: How often to import (hours)
        auth_type: Authentication method (none, api_key, oauth, etc.)
        parser_type: Which parser to use (json, csv, html, xml)
        last_run_at: When the last import job ran
        last_success_at: When the last successful import completed
        status: Current status (ok, error, inactive, testing)
        notes: Admin notes about this source
        created_at: When this source was registered
        updated_at: Last modification time
    """
    
    __tablename__ = "lead_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # api, scraper, csv, webhook, etc.
    sector = Column(String(100), nullable=True)  # wholesaling, real_estate, etc.
    base_url = Column(String(500), nullable=True)
    active = Column(Boolean, default=True, index=True)
    scrape_frequency = Column(Integer, default=24)  # hours between imports
    auth_type = Column(String(50), default="none")  # none, api_key, oauth, etc.
    parser_type = Column(String(50), default="json")  # json, csv, html, xml
    last_run_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="inactive")  # ok, error, inactive, testing
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    raw_leads = relationship("RawLead", back_populates="source", cascade="all, delete-orphan")
    normalized_leads = relationship("NormalizedLead", back_populates="source", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LeadSource(id={self.id}, name={self.name}, source_type={self.source_type})>"
