"""
PACK L0-09: Strategic Decision Model
Stores strategic decisions with context, rationale, and approval workflow.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import Base


class StrategicDecision(Base):
    """
    A strategic decision proposal with evaluation and approval workflow.
    
    Lifecycle:
    PENDING -> APPROVED/REJECTED -> EXECUTED/ABANDONED
    
    Marked as stable schema (STABLE CONTRACT).
    """
    
    __tablename__ = "strategic_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    
    # Reference to the strategic mode under which this was proposed
    mode_id = Column(Integer, ForeignKey("strategic_modes.id"), nullable=True)
    mode = relationship("StrategicMode")
    
    # Context that led to this decision
    # Example: {
    #   "trigger": "new_deal_opportunity",
    #   "deal_id": 123,
    #   "market_conditions": {...},
    #   "cash_available": 100000
    # }
    input_context = Column(JSON, nullable=False, default={})
    
    # The recommendation/proposal
    # Example: {
    #   "action": "acquire_wholesale_deal",
    #   "target_property": "123 Main St, Toronto",
    #   "proposed_offer": 250000,
    #   "estimated_arv": 350000,
    #   "rationale": "Strong wholesale spread, cash flow positive",
    #   "expected_outcomes": {
    #     "cashflow_annual": 12000,
    #     "equity_built": 100000
    #   }
    # }
    recommendation = Column(JSON, nullable=False, default={})
    
    # Confidence in the recommendation
    confidence_score = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0
    
    # Risk assessment
    # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    risk_level = Column(String(20), nullable=False, default="MEDIUM")
    
    # Status in approval workflow
    # PENDING -> APPROVED -> EXECUTED
    # PENDING -> REJECTED
    # PENDING -> WITHDRAWN
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    
    # Who reviewed/approved
    reviewer = Column(String(100), nullable=True)  # user_id or "system"
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_tenant_status", "tenant_id", "status"),
        Index("idx_mode_timestamp", "mode_id", "timestamp"),
        Index("idx_confidence", "confidence_score"),
    )
    
    def __repr__(self) -> str:
        return f"<StrategicDecision(id={self.id}, tenant_id={self.tenant_id}, status={self.status})>"
