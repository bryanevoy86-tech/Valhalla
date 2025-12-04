from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class BahamasVault(Base):
    __tablename__ = "bahamas_vault"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="Bahamas Residency Vault")
    current_balance = Column(Float, default=0.0)
    target_balance = Column(Float, default=0.0)
    min_resort_price = Column(Float, default=0.0)
    max_resort_price = Column(Float, default=0.0)
    percent_to_target = Column(Float, default=0.0)
    residency_ready = Column(Boolean, default=False)
    resort_search_active = Column(Boolean, default=False)
    notes = Column(Text)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
