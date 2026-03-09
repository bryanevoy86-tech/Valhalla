from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class BRRRRZone(Base):
    __tablename__ = "brrrr_zones"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    min_properties_before_team = Column(Integer, default=5)
    current_property_count = Column(Integer, default=0)
    currency = Column(String, default="CAD")
    language = Column(String, default="en")
    timezone = Column(String, default="UTC")
    active = Column(Boolean, default=False)
    legal_profile_code = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
