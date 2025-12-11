"""
PACK L0-09: Tuning Rules Model
Decision thresholds and tuning rules for strategic decisions.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Index

from app.models.base import Base


class TuningRule(Base):
    """
    A tuning rule for decision-making thresholds and parameters.
    
    Examples:
    - "max_deal_value": {"threshold": 500000, "unit": "CAD"}
    - "min_cashflow_required": {"threshold": 12000, "unit": "CAD/year"}
    - "avoid_overlapping_projects": {"rule_type": "toggle", "value": true}
    - "require_approval_above": {"threshold": 250000, "unit": "CAD"}
    
    Rules are evaluated before decisions are marked APPROVED/EXECUTED.
    
    Marked as stable schema (STABLE CONTRACT).
    """
    
    __tablename__ = "tuning_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    
    # Rule identity
    name = Column(String(100), nullable=False)  # e.g., "max_concurrent_deals"
    description = Column(String(500), nullable=True)
    
    # Rule type: "threshold", "toggle", "percentage", "choice", etc.
    rule_type = Column(String(50), nullable=False, default="threshold")
    
    # Rule configuration
    # Example: {"threshold": 500000, "unit": "CAD", "operator": "lte"}
    # Example: {"rule_type": "toggle", "value": true}
    config = Column(JSON, nullable=False, default={})
    
    # Activation
    active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_tenant_rule", "tenant_id", "name"),
        Index("idx_active_rules", "tenant_id", "active"),
    )
    
    def __repr__(self) -> str:
        return f"<TuningRule(id={self.id}, tenant_id={self.tenant_id}, name={self.name}, active={self.active})>"
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
