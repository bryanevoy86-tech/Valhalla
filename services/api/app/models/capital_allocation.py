"""PACK 62: Capital Allocation Engine
Capital distribution across arbitrage, vault, and shield pools.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime

from app.models.base import Base


class CapitalAllocation(Base):
    __tablename__ = "capital_allocation"

    id = Column(Integer, primary_key=True, index=True)
    arbitrage_pct = Column(Float, nullable=False)
    vault_pct = Column(Float, nullable=False)
    shield_pct = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
