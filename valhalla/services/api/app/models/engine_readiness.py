"""
Engine readiness tracking - state machine for engine promotion.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.core.db import Base


class EngineReadiness(Base):
    __tablename__ = "engine_readiness"

    id = Column(Integer, primary_key=True)
    engine_name = Column(String(64), unique=True, nullable=False, index=True)

    # Current state: DISABLED | SANDBOX | READY | LIVE
    state = Column(String(16), nullable=False, default="DISABLED")

    # Metrics (updated daily or on-demand)
    approval_rate = Column(Float, nullable=True)  # For wholesaling
    false_positive_rate = Column(Float, nullable=True)  # For wholesaling
    sample_size = Column(Integer, nullable=True)  # Number of decisions

    # Last evaluation timestamp
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<EngineReadiness(engine={self.engine_name}, state={self.state}, approval_rate={self.approval_rate}, fp_rate={self.false_positive_rate})>"
