from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from datetime import datetime, timezone
from app.core.db import Base


class FXRule(Base):
    __tablename__ = "fx_rules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "SafeMode Max DD 2%"
    param = Column(String, nullable=False)  # e.g., "max_drawdown_pct"
    value = Column(Float, nullable=False)  # e.g., 2.0
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FXOrder(Base):
    __tablename__ = "fx_orders"
    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String, nullable=False)  # e.g., "EUR/CAD"
    side = Column(String, nullable=False)  # "buy"|"sell"
    size = Column(Float, nullable=False)  # units or notional
    entry_px = Column(Float, nullable=False)
    exit_px = Column(Float, nullable=True)
    status = Column(String, default="open")  # open|filled|closed|cancelled
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)


class FXMetric(Base):
    __tablename__ = "fx_metrics"
    id = Column(Integer, primary_key=True, index=True)
    equity = Column(Float, default=0.0)  # running equity of FX book
    peak_equity = Column(Float, default=0.0)
    drawdown_pct = Column(Float, default=0.0)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
