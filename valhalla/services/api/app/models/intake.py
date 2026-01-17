from sqlalchemy import Column, Integer, String, Numeric, DateTime, func
from ..core.db import Base

class CapitalIntake(Base):
    __tablename__ = "capital_intake"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=False)                   # e.g., "wholesaling", "grants", "jv"
    amount = Column(Numeric(18, 2), nullable=False)                # gross intake
    currency = Column(String(10), default="CAD", nullable=False)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
