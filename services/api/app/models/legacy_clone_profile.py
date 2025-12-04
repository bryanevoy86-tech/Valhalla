from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class LegacyCloneProfile(Base):
    __tablename__ = "legacy_clone_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    min_monthly_income = Column(Float, default=0.0)
    min_reserve_months = Column(Float, default=2.0)
    min_legacy_count = Column(Integer, default=1)
    max_legacies = Column(Integer, default=100)
    require_all_green_health = Column(Boolean, default=True)
    auto_clone_enabled = Column(Boolean, default=True)
    clones_per_batch = Column(Integer, default=1)
    max_new_clones_per_year = Column(Integer, default=10)
    notes = Column(Text)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
