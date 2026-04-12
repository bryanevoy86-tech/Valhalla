"""
ExecutionEvent model - immutable audit trail for execution case
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.core.db import Base


class ExecutionEvent(Base):
    """
    Execution event - logs every action/state change in a case.
    Immutable (never updated).
    """
    __tablename__ = "execution_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    case_id = Column(Integer, ForeignKey("execution_cases.id"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # classified, assessed, routed, task_created, advanced, blocked, closed
    stage_from = Column(String(50), nullable=True)   # Previous stage (if transition)
    stage_to = Column(String(50), nullable=True)     # New stage (if transition)
    action_description = Column(Text, nullable=True) # Human-readable description
    
    # Event payload (JSON details of what happened)
    payload_json = Column(Text, nullable=False, default="{}")
    
    # Audit info
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actor = Column(String(100), nullable=False, default="system")
    
    def __repr__(self):
        return f"<ExecutionEvent #{self.id} | {self.event_type} @ {self.created_at}>"
