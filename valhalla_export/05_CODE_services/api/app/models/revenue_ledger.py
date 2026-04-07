from __future__ import annotations
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, Index
from app.models.base import Base

class RevenueLedger(Base):
    __tablename__ = "revenue_ledger"

    id = Column(Integer, primary_key=True, index=True)

    engine_code = Column(String, nullable=False)
    source_ref = Column(String, nullable=True)

    currency = Column(String, nullable=False, default="USD")
    gross_amount = Column(Numeric(18, 2), nullable=False, default=0)

    fun_fund_amount = Column(Numeric(18, 2), nullable=False, default=0)
    reinvest_amount = Column(Numeric(18, 2), nullable=False, default=0)
    ops_reserve_amount = Column(Numeric(18, 2), nullable=False, default=0)

    as_of_date = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


Index("ix_revenue_ledger_engine_date", RevenueLedger.engine_code, RevenueLedger.as_of_date)
