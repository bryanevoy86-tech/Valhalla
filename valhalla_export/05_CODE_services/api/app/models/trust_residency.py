"""
PACK AU: Trust & Residency Profile Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float
from app.models.base import Base


class TrustResidencyProfile(Base):
    """
    Operational trust & residency profiles for users, professionals, vendors, tenants.
    Tracks jurisdiction and internal trust/footprint scores based on behavior.
    """
    __tablename__ = "trust_residency_profiles"

    id = Column(Integer, primary_key=True, index=True)

    # who / what this refers to
    subject_type = Column(String, nullable=False)   # user, professional, vendor, tenant, etc.
    subject_id = Column(String, nullable=False)     # ID in your system

    # high-level jurisdiction info (non-legal)
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)          # province/state/region
    city = Column(String, nullable=True)

    # internal trust / footprint scores (0–100)
    trust_score = Column(Float, nullable=False, default=50.0)
    footprint_score = Column(Float, nullable=False, default=0.0)

    notes = Column(String, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
