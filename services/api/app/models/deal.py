"""Backend Deal model - canonical for Heimdall operations."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Core deal information
    title = Column(String(255), nullable=False)
    stage = Column(String(50), nullable=False)  # pipeline stage
    status = Column(String(50), nullable=False, default="active")  # active, closed, dead, etc.
    
    # Financial metrics (stored as DECIMAL in DB, Numeric in SQLAlchemy)
    arv = Column(Numeric(15, 2), nullable=True)  # After Repair Value
    estimated_repair_cost = Column(Numeric(15, 2), nullable=True)
    max_allowable_offer = Column(Numeric(15, 2), nullable=True)
    target_assignment_fee = Column(Numeric(15, 2), nullable=True)
    score = Column(Numeric(8, 2), nullable=True)  # Heimdall score
    
    # Metadata
    notes = Column(Text, nullable=True)
    disposition_status = Column(String(50), nullable=True)
    
    # Relationships
    lead = relationship("Lead", foreign_keys=[lead_id]) if 'Lead' in locals() else None
