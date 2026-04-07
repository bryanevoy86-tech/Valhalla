from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, UniqueConstraint
from app.models.base import Base

class IncomeEngine(Base):
    __tablename__ = "income_engines"
    __table_args__ = (UniqueConstraint("code", name="uq_income_engines_code"),)

    id = Column(Integer, primary_key=True, index=True)

    code = Column(String, nullable=False)          # e.g. REAL_ESTATE_WHOLESALE, BRRRR, FLIPS, ARBITRAGE, AI_SAAS...
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)      # REAL_ESTATE, CAPITAL, AI_NATIVE, LICENSING, TREASURY, ENERGY, etc.
    description = Column(String, nullable=True)

    # Lifecycle: DESIGNED, BUILT, TESTING, PAPER, LIVE, PAUSED, DEPRECATED
    status = Column(String, nullable=False, default="DESIGNED")

    # Governance
    requires_approval = Column(Boolean, nullable=False, default=True)
    sandbox_only = Column(Boolean, nullable=False, default=True)

    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
