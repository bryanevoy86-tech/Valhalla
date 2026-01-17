from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, UniqueConstraint
from app.models.base import Base


class RiskPolicy(Base):
    """
    Institutional-grade risk floors.
    One row per engine (plus a GLOBAL row).
    """
    __tablename__ = "risk_policy"
    __table_args__ = (UniqueConstraint("engine", name="uq_risk_policy_engine"),)

    id = Column(Integer, primary_key=True, index=True)
    engine = Column(String, nullable=False)  # e.g. "GLOBAL", "WHOLESALE", "CAPITAL", "NOTIFY"

    # Hard caps (daily, per engine)
    max_daily_loss = Column(Float, nullable=False, default=0.0)        # absolute dollars
    max_daily_exposure = Column(Float, nullable=False, default=0.0)    # dollars "at risk"
    max_open_risk = Column(Float, nullable=False, default=0.0)         # reserved but not settled

    # Optional throttles (soft, but enforceable if you want)
    max_actions_per_day = Column(Integer, nullable=False, default=0)    # 0 => disabled/unlimited

    # If disabled, engine cannot execute production actions
    enabled = Column(Boolean, nullable=False, default=True)

    changed_by = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
