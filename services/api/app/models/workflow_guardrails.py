"""
PACK L0-09: Workflow Guardrails Model
Safety guardrails to prevent unsafe strategic decisions.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Index

from app.models.base import Base


class WorkflowGuardrail(Base):
    """
    A workflow guardrail that enforces safety constraints on decision workflows.
    
    Examples:
    - Require manager approval for deals > $500k
    - Block decisions during market volatility
    - Require 24-hour review period for major changes
    - Prevent concurrent overlapping projects
    
    Guardrails are checked before marking decisions APPROVED/EXECUTED.
    
    Marked as stable schema (STABLE CONTRACT).
    """
    
    __tablename__ = "workflow_guardrails"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    
    # Guardrail identity
    name = Column(String(100), nullable=False)  # e.g., "high_value_deal_approval"
    description = Column(String(500), nullable=True)
    
    # What routes/modules this applies to
    # Example: "wholesale_deals", "real_estate", "*" for all
    applies_to = Column(String(100), nullable=False, default="*")
    
    # Condition that triggers this guardrail
    # Example: {"field": "deal_value", "operator": "gte", "value": 500000}
    # Example: {"field": "market_volatility", "operator": "gte", "value": 0.8}
    condition = Column(JSON, nullable=False, default={})
    
    # How many reviews/approvals are required when triggered
    required_reviews = Column(Integer, nullable=False, default=1)
    
    # Auto-block vs warn
    # true = block execution, false = warn but allow override
    auto_block = Column(Boolean, nullable=False, default=False)
    
    # Activation
    active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_tenant_guardrail", "tenant_id", "name"),
        Index("idx_applies_to", "applies_to", "active"),
    )
    
    def __repr__(self) -> str:
        return f"<WorkflowGuardrail(id={self.id}, tenant_id={self.tenant_id}, name={self.name}, active={self.active})>"
