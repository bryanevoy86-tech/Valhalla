"""
PACK L0-09: Trajectory Model
Long-term trajectory planning and projection.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index

from app.models.base import Base


class Trajectory(Base):
    """
    Long-term trajectory for a tenant.
    
    Represents current projections, target states, and strategic horizon.
    Example: "3-month trajectory toward real estate diversification"
    
    Marked as stable schema (STABLE CONTRACT).
    """
    
    __tablename__ = "trajectories"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    
    # Horizon: "3m", "6m", "12m", "3y", "5y", "10y", etc.
    horizon = Column(String(20), nullable=False, default="12m")
    
    # Target state: where we want to be
    # Example: {
    #   "description": "Diversified real estate portfolio with 5-10 properties",
    #   "key_metrics": {
    #     "properties_owned": 8,
    #     "annual_cashflow": 150000,
    #     "net_worth": 2500000
    #   }
    # }
    target_state = Column(JSON, nullable=False, default={})
    
    # Current projection: where we're headed
    # Example: {
    #   "description": "On track for 3 properties by end of year",
    #   "confidence": 0.75,
    #   "key_metrics": {
    #     "properties_owned": 3,
    #     "annual_cashflow": 45000,
    #     "net_worth": 750000
    #   },
    #   "risks": ["market_downturn", "financing_difficulty"]
    # }
    current_projection = Column(JSON, nullable=False, default={})
    
    # Roadmap: milestones to reach target
    # Example: [
    #   {"date": "2025-Q1", "milestone": "Close first wholesale deal"},
    #   {"date": "2025-Q2", "milestone": "Begin rehab on first property"}
    # ]
    roadmap = Column(JSON, nullable=True, default=[])
    
    # Risk assessment
    risk_factors = Column(JSON, nullable=True, default=[])
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_tenant_trajectory", "tenant_id", "horizon"),
    )
    
    def __repr__(self) -> str:
        return f"<Trajectory(id={self.id}, tenant_id={self.tenant_id}, horizon={self.horizon})>"
