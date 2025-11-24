from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime

class LegalProfile(Base):
    __tablename__ = "legal_profiles"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String, nullable=False)          # e.g. "Canada", "Panama"
    region = Column(String)                           # province/state/zone
    profile_name = Column(String, nullable=False)     # "BRRRR Rules", "Landlord-Tenant Laws"

    category = Column(String)                         # "BRRRR", "RENTAL", "TAX", "TRUST", etc.
    risk_level = Column(String, default="medium")     # low / medium / high
    notes = Column(Text)                              # summary of the rules
    active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
