from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime


class BahamasPlan(Base):
    __tablename__ = "bahamas_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="Bahamas Residency & Resort Plan")

    residency_target = Column(Float, nullable=False)        # amount needed to qualify
    residency_vault_balance = Column(Float, default=0.0)

    resort_target_price_min = Column(Float, default=0.0)
    resort_target_price_max = Column(Float, default=0.0)
    resort_vault_balance = Column(Float, default=0.0)

    trigger_residency_ready = Column(Boolean, default=False)
    trigger_resort_search_active = Column(Boolean, default=False)

    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
