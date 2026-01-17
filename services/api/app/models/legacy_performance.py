from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class LegacyPerformance(Base):
    __tablename__ = "legacy_performance"

    id = Column(Integer, primary_key=True, index=True)
    legacy_code = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    period = Column(String, default="month")
    period_label = Column(String, nullable=False)
    gross_income = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)
    reinvestment = Column(Float, default=0.0)
    fun_fund = Column(Float, default=0.0)
    deals_closed = Column(Integer, default=0)
    brRRR_units = Column(Integer, default=0)
    flips = Column(Integer, default=0)
    wholesale_deals = Column(Integer, default=0)
    risk_flag = Column(Boolean, default=False)
    risk_note = Column(Text)
    status = Column(String, default="normal")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
