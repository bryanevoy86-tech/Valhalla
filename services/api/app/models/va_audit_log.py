"""
VA Audit Log model - tracks all VA intake operations for compliance and debugging.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from ..core.db import Base


class VAAuditLog(Base):
    __tablename__ = "va_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Actor and action
    actor = Column(String(80), nullable=False)  # "system", "va", "bryan", user email, etc.
    action = Column(String(100), nullable=False)  # "lead_submitted", "lead_scored", "approval_approved", etc.
    
    # Entity being acted upon
    entity_type = Column(String(60), nullable=False, default="va_lead")  # va_lead, approval, deal, etc.
    entity_id = Column(Integer, nullable=False, index=True)
    
    # Details
    details = Column(Text, nullable=True)  # JSON or structured info
    
    # Change tracking
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="success")  # success, error, warning
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
