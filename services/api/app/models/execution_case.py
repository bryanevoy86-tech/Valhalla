"""
ExecutionCase model - tracks entire lifecycle of an opportunity execution
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, ForeignKey, func
)
from datetime import datetime
from app.core.db import Base


class ExecutionCase(Base):
    """
    Execution case - one per opportunity being processed.
    Links LeadIntake → UnderwriterAssessment → Execution Tasks.
    """
    __tablename__ = "execution_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    intake_id = Column(Integer, ForeignKey("lead_intake_exec.id"), nullable=False, unique=True)
    assessment_id = Column(Integer, ForeignKey("underwriter_assessments.id"), nullable=True)
    
    # Classification & routing
    case_type = Column(String(50), nullable=False, default="unknown")
    route_target = Column(String(100), nullable=False, default="")
    
    # State tracking
    current_stage = Column(String(50), nullable=False, default="intake")
    current_status = Column(String(50), nullable=False, default="pending")
    
    # Safety & control
    safe_mode = Column(Boolean, nullable=False, default=False)
    blocked = Column(Boolean, nullable=False, default=False)
    blocker_reason = Column(Text, nullable=True)
    
    # Operator guidance
    next_action = Column(Text, nullable=False, default="")
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100), nullable=False, default="system")
    updated_by = Column(String(100), nullable=False, default="system")
    
    def __repr__(self):
        return f"<ExecutionCase #{self.id} | {self.case_type} @ {self.current_stage}>"
