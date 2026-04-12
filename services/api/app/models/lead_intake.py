"""
LeadIntake model - simple raw opportunity text capture for execution layer
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.db import Base


class LeadIntake(Base):
    """
    Raw opportunity intake - captures unstructured text from operator paste.
    
    This is the entry point for the execution layer.
    V1 design: dead-simple, just store the raw text and metadata.
    
    Workflow:
    1. Operator pastes raw opportunity -> LeadIntake record created
    2. Click "Process" -> Execution layer parses, classifies, assesses, routes
    3. ExecutionCase record created, linked to this intake
    
    Fields:
        id: Unique identifier
        raw_text: Unstructured text pasted by operator
        source_type: Where this came from (manual_entry, email, form, etc)
        status: new | normalized | archived | duplicate
        created_at: When recorded
        created_by: Who created (operator ID or "system")
        normalized_at: When execution layer processed it
    """
    
    __tablename__ = "lead_intake_exec"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text, nullable=False)
    source_type = Column(String(50), default="manual_entry", nullable=False)
    status = Column(String(50), default="new", nullable=False, index=True)  # new, normalized, archived, duplicate
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by = Column(String(50), default="operators", nullable=False)
    normalized_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return (
            f"<LeadIntake(id={self.id}, status={self.status}, "
            f"source_type={self.source_type}, created_at={self.created_at})>"
        )
