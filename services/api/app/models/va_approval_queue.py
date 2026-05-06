"""
VA Approval Queue model - tracks leads pending approval.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from ..core.db import Base


class VAApprovalQueue(Base):
    __tablename__ = "va_approval_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Entity being approved
    entity_type = Column(String(60), nullable=False, default="lead")  # lead, seller_contact, deal, etc.
    entity_id = Column(Integer, nullable=False, index=True)
    va_lead_id = Column(Integer, nullable=False, index=True)  # Direct reference to VA lead
    
    # Approval details
    status = Column(String(60), nullable=False, default="pending")  # pending, approved, denied, cancelled
    recommended_action = Column(String(255), nullable=True)
    heimdall_score = Column(Integer, nullable=True)
    risk_level = Column(String(20), nullable=True)  # low, medium, high
    
    # Approval metadata
    assigned_to = Column(String(80), nullable=True)  # who should approve (e.g., "bryan")
    approved_by = Column(String(80), nullable=True)  # who actually approved
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    denied_by = Column(String(80), nullable=True)
    denied_at = Column(DateTime(timezone=True), nullable=True)
    denial_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
