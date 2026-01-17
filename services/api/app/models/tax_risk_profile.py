from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class TaxRiskProfile(Base):
    __tablename__ = "tax_risk_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    jurisdiction = Column(String, nullable=False, default="CRA")
    risk_level = Column(Float, default=0.5)
    meals_percent_cap = Column(Float, default=0.10)
    vehicle_percent_cap = Column(Float, default=0.30)
    home_office_percent_cap = Column(Float, default=0.20)
    travel_percent_cap = Column(Float, default=0.15)
    auto_flag_red = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
