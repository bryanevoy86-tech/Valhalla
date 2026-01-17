from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.base_class import Base
import datetime


class KpiMetric(Base):
    __tablename__ = "kpi_metrics"

    id = Column(Integer, primary_key=True, index=True)
    # e.g. "revenue", "profit", "fun_fund", "reinvestment", "vault_balance"
    name = Column(String, nullable=False)

    # scope: empire, legacy, trust, zone, etc.
    scope = Column(String, default="empire")
    scope_ref = Column(String)

    # timescale: "month", "day", etc. value for that period
    period = Column(String, default="month")
    period_label = Column(String, nullable=False)

    value = Column(Float, default=0.0)
    currency = Column(String, default="CAD")

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
