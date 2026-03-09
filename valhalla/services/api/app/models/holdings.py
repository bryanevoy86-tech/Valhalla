"""
PACK Z: Global Holdings Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from app.models.base import Base


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)

    asset_type = Column(
        String,
        nullable=False,
    )  # property, resort, note, trust_interest, policy, saas_stream, vault, etc.

    # Reference to the underlying system (e.g. property_id, policy_id, etc.)
    internal_ref = Column(String, nullable=True)

    jurisdiction = Column(String, nullable=True)   # country or region
    entity_name = Column(String, nullable=True)    # trust/company name
    entity_id = Column(String, nullable=True)      # internal id in your trust/company system

    label = Column(String, nullable=True)          # human label, e.g. "Bahamas Resort 1"
    notes = Column(String, nullable=True)

    value_estimate = Column(Float, nullable=True)
    currency = Column(String, nullable=True, default="USD")

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
