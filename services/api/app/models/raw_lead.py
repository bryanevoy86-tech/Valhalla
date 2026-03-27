"""
Raw Lead model - stores unprocessed lead data from external sources.

This is the first stage in the lead pipeline: raw data is ingested from sources,
then normalized, then deduplicated, then scored and routed.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class RawLead(Base):
    """
    Stores raw lead data as received from external sources.
    
    Fields:
        id: Unique identifier
        source_id: Which lead source this came from
        raw_hash: Hash of raw_data for dedupe detection
        raw_data: Complete raw payload from source (JSON)
        imported_at: When this raw lead was ingested
        status: processing status (pending, normalized, error, skipped)
        notes: Processing notes or error messages
    """
    
    __tablename__ = "raw_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("lead_sources.id"), nullable=False, index=True)
    raw_hash = Column(String(64), nullable=False, index=True)  # SHA256 hash for dedupe
    raw_data = Column(JSON, nullable=False)  # Complete payload from source
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = Column(String(20), default="pending")  # pending, normalized, error, skipped
    notes = Column(Text, nullable=True)
    
    # Relationships
    source = relationship("LeadSource", back_populates="raw_leads")
    
    def __repr__(self):
        return f"<RawLead(id={self.id}, source_id={self.source_id})>"
