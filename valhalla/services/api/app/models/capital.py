"""
Capital intake model for tracking incoming funds from various sources.
"""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, func
from ..core.db import Base


class CapitalIntake(Base):
    __tablename__ = "capital_intake"
    
    id = Column(Integer, primary_key=True)
    source = Column(String(120), nullable=False)  # e.g., "wholesaling", "fx", "flip"
    currency = Column(String(12), nullable=False, default="CAD")
    amount = Column(Numeric(18, 2), nullable=False)
    note = Column(String(280), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
