from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, UniqueConstraint
from app.models.base import Base


class RiskLedgerDay(Base):
    """
    Daily ledger for risk usage.
    Tracks totals so guard can enforce floors quickly and safely.
    """
    __tablename__ = "risk_ledger_day"
    __table_args__ = (UniqueConstraint("day", "engine", name="uq_risk_ledger_day_engine"),)

    id = Column(Integer, primary_key=True, index=True)
    day = Column(Date, nullable=False)                 # local day (use UTC date to stay consistent)
    engine = Column(String, nullable=False)            # same engine tags as RiskPolicy

    # Totals
    exposure_used = Column(Float, nullable=False, default=0.0)         # how much exposure consumed today
    open_risk_reserved = Column(Float, nullable=False, default=0.0)    # risk reserved but not settled
    realized_loss = Column(Float, nullable=False, default=0.0)         # realized losses today
    actions_count = Column(Integer, nullable=False, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
