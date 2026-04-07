from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, UniqueConstraint
from app.models.base import Base


class RegressionState(Base):
    """
    Current tripwire status for (domain, metric).
    """
    __tablename__ = "regression_state"
    __table_args__ = (UniqueConstraint("domain", "metric", name="uq_regression_state_domain_metric"),)

    id = Column(Integer, primary_key=True, index=True)

    domain = Column(String, nullable=False)
    metric = Column(String, nullable=False)

    triggered = Column(Boolean, nullable=False, default=False)
    baseline = Column(Float, nullable=True)
    current = Column(Float, nullable=True)
    drop_fraction = Column(Float, nullable=True)

    last_checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)

    note = Column(String, nullable=True)
