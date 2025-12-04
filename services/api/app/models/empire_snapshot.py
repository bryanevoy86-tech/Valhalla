from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
import datetime
from app.db.base_class import Base


class EmpireSnapshot(Base):
    __tablename__ = "empire_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    # Original fields (retain for backward compatibility)
    label = Column(String, nullable=True)
    snapshot_type = Column(String, default="manual")
    summary_json = Column(Text, nullable=True)
    notes = Column(Text)

    # Pack 110 expanded metric surface
    period = Column(String, nullable=True, default="month")
    period_label = Column(String, nullable=True)
    gross_income = Column(Float, default=0.0)
    taxes_reserved = Column(Float, default=0.0)
    reinvestment = Column(Float, default=0.0)
    fun_fund = Column(Float, default=0.0)
    legacy_count = Column(Integer, default=0)
    active_zones = Column(Integer, default=0)
    brRRR_count = Column(Integer, default=0)
    flip_count = Column(Integer, default=0)
    wholesale_count = Column(Integer, default=0)
    resort_count = Column(Integer, default=0)
    shield_mode_active = Column(Boolean, default=False)
    black_ice_armed = Column(Boolean, default=False)
    bahamas_ready = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

__all__ = ["EmpireSnapshot"]
