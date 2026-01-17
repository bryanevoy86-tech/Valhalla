from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class LegalProfile(Base):
    __tablename__ = "legal_profiles"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, unique=True)
    country = Column(String, nullable=False)
    region = Column(String)
    description = Column(Text)
    requires_local_corp = Column(Boolean, default=False)
    allows_foreign_ownership = Column(Boolean, default=True)
    brrrr_refi_restricted = Column(Boolean, default=False)
    short_term_rental_restricted = Column(Boolean, default=False)
    eviction_strict = Column(Boolean, default=False)
    license_required = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
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
