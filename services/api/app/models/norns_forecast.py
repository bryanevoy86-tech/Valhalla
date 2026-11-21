"""Timestamped estimates and measured internal Factory outcomes."""
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, JSON, String, Uuid

from app.core.db import Base


class NornsForecast(Base):
    __tablename__ = "prime_norns_forecasts"
    __table_args__ = (
        CheckConstraint("probability_bp BETWEEN 0 AND 10000", name="ck_norns_probability_bp"),
        CheckConstraint("observed_outcome IS NULL OR observed_outcome IN (0, 1)", name="ck_norns_binary_outcome"),
    )
    id = Column(Uuid(), primary_key=True)
    action_id = Column(String(80), nullable=False, unique=True)
    probability_bp = Column(Integer(), nullable=False)
    issued_at = Column(DateTime(), nullable=False)
    deadline_at = Column(DateTime(), nullable=False)
    resolved_at = Column(DateTime())
    observed_outcome = Column(Integer())
    evidence_ref = Column(String(180))
    estimate_source = Column(String(40), nullable=False, server_default="OWNER_ESTIMATE")
    training_evidence = Column(JSON())


class NornsHoldout(Base):
    """A prospective enrollment excluded from historical-rate training."""
    __tablename__ = "prime_norns_holdout"

    forecast_id = Column(Uuid(), ForeignKey("prime_norns_forecasts.id"), primary_key=True)
    enrolled_at = Column(DateTime(), nullable=False)


class NornsMarketForecast(Base):
    """Prospective market thresholds scored against a pinned second source."""
    __tablename__ = "prime_norns_market_forecasts"
    __table_args__ = (
        CheckConstraint("probability_bp BETWEEN 0 AND 10000", name="ck_market_forecast_probability"),
        CheckConstraint("observed_outcome IS NULL OR observed_outcome IN (0, 1)", name="ck_market_forecast_outcome"),
    )
    id = Column(Uuid(), primary_key=True)
    scope_key = Column(String(64), nullable=False, index=True)
    target_key = Column(String(64), nullable=False, unique=True)
    evidence_class = Column(String(20), nullable=False)
    probability_bp = Column(Integer(), nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=False)
    payload = Column(JSON(), nullable=False)
    digest = Column(String(64), nullable=False)
    observed_outcome = Column(Integer())
    settlement = Column(JSON())
