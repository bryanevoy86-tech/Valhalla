from __future__ import annotations
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, UniqueConstraint
from app.models.base import Base

class TrajectoryTarget(Base):
    __tablename__ = "trajectory_targets"
    __table_args__ = (UniqueConstraint("engine_code", "month", name="uq_targets_engine_month"),)

    id = Column(Integer, primary_key=True, index=True)
    engine_code = Column(String, nullable=False, default="SYSTEM")
    month = Column(Date, nullable=False)  # store as first day of month

    currency = Column(String, nullable=False, default="USD")
    min_gross = Column(Numeric(18, 2), nullable=False, default=0)
    min_fun_fund = Column(Numeric(18, 2), nullable=False, default=0)

    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
