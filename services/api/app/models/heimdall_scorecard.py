from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, UniqueConstraint
from app.models.base import Base


class HeimdallScorecardDay(Base):
    """
    Daily sandbox scorecard per domain.
    Tracks aggregate performance so the gate can enforce regression controls.
    """
    __tablename__ = "heimdall_scorecard_day"
    __table_args__ = (UniqueConstraint("day", "domain", name="uq_heimdall_scorecard_day_domain"),)

    id = Column(Integer, primary_key=True, index=True)
    day = Column(Date, nullable=False)
    domain = Column(String, nullable=False)

    trials = Column(Integer, nullable=False, default=0)
    successes = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float, nullable=False, default=0.0)

    avg_confidence = Column(Float, nullable=False, default=0.0)

    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
