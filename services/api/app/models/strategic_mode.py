"""
PACK L0-09: Strategic Mode Model
Defines operational modes (aggressive, conservative, defensive, etc.) with parameters.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Index

from app.models.base import Base


class StrategicMode(Base):
    """
    Strategic mode definition for a tenant.
    
    A strategic mode encodes decision parameters, risk tolerance, and operational style.
    Examples: "aggressive", "conservative", "defensive", "growth", "optimization".
    
    Multiple modes can exist; one marked as active for current use.
    
    Marked as stable schema (STABLE CONTRACT).
    """
    
    __tablename__ = "strategic_modes"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    
    # Mode identity
    name = Column(String(100), nullable=False)  # "aggressive", "conservative", etc.
    description = Column(String(500), nullable=True)
    
    # Mode parameters (JSON object)
    # Example: {
    #   "risk_tolerance": 0.8,  # 0.0 = avoid all risk, 1.0 = max risk appetite
    #   "growth_weight": 0.6,   # how much we prioritize growth vs stability
    #   "speed_weight": 0.5,    # how much we prioritize fast decisions vs thorough
    #   "compliance_weight": 1.0,  # compliance is always critical
    #   "investment_horizon": "3-5 years",
    #   "max_concurrent_projects": 5,
    # }
    parameters = Column(JSON, nullable=False, default={})
    
    # Activation
    active = Column(Boolean, nullable=False, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_tenant_mode", "tenant_id", "name"),
        Index("idx_tenant_active", "tenant_id", "active"),
    )
    
    def __repr__(self) -> str:
        return f"<StrategicMode(id={self.id}, tenant_id={self.tenant_id}, name={self.name}, active={self.active})>"
