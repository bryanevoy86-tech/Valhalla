from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, UniqueConstraint
from app.models.base import Base


class HeimdallPolicy(Base):
    """
    Confidence Charter: thresholds that govern when Heimdall recommendations
    may be used for production execution.
    """
    __tablename__ = "heimdall_policy"
    __table_args__ = (UniqueConstraint("domain", name="uq_heimdall_policy_domain"),)

    id = Column(Integer, primary_key=True, index=True)

    # Domain examples: "WHOLESALE_OFFER", "BUYER_MATCH", "CAPITAL_ROUTE", "FOLLOWUP_NEXT_ACTION"
    domain = Column(String, nullable=False)

    # Minimum confidence required to allow production execution driven by this recommendation.
    min_confidence_prod = Column(Float, nullable=False, default=0.90)

    # Minimum number of sandbox trials required before prod use is allowed.
    min_sandbox_trials = Column(Integer, nullable=False, default=50)

    # Minimum sandbox success rate required.
    min_sandbox_success_rate = Column(Float, nullable=False, default=0.80)

    # If False, Heimdall recommendations in this domain are advisory only (cannot be used to execute).
    prod_use_enabled = Column(Boolean, nullable=False, default=False)

    changed_by = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
