from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class ShieldProfile(Base):
    __tablename__ = "shield_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    min_reserve_months = Column(Float, default=2.0)
    max_active_expansions = Column(Integer, default=3)
    income_drop_percent = Column(Float, default=0.30)
    pause_new_clones = Column(Boolean, default=True)
    pause_new_zones = Column(Boolean, default=True)
    reduce_marketing_spend = Column(Boolean, default=True)
    stop_fun_fund_increase = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
