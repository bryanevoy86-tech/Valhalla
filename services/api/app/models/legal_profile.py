from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
import datetime
from app.models.base import Base


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
