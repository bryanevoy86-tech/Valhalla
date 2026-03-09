from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, UniqueConstraint
from app.models.base import Base


class RegressionPolicy(Base):
    """
    Defines regression thresholds per (domain, metric).
    """
    __tablename__ = "regression_policy"
    __table_args__ = (UniqueConstraint("domain", "metric", name="uq_regression_policy_domain_metric"),)

    id = Column(Integer, primary_key=True, index=True)

    domain = Column(String, nullable=False)
    metric = Column(String, nullable=False)

    # Window & baseline
    window_events = Column(Integer, nullable=False, default=50)       # evaluate last N events
    baseline_events = Column(Integer, nullable=False, default=200)    # compare vs prior N events
    min_events_to_enforce = Column(Integer, nullable=False, default=50)

    # Trigger when performance drops more than this fraction vs baseline.
    # Example: 0.20 means "20% drop from baseline triggers tripwire"
    max_drop_fraction = Column(Float, nullable=False, default=0.20)

    # What to do if triggered:
    # - "THROTTLE": set engine risk policy enabled=False (safe, reversible)
    # - "KILL_SWITCH": engage kill-switch
    action = Column(String, nullable=False, default="THROTTLE")

    enabled = Column(Boolean, nullable=False, default=True)

    changed_by = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
