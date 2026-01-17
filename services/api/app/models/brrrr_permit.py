"""PACK 72: BRRRR Value & Permit Package Engine
BRRRR analysis and permit package generation.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text

from app.models.base import Base


class BrrrrAnalysis(Base):
    __tablename__ = "brrrr_analysis"

    id = Column(Integer, primary_key=True, index=True)
    property_address = Column(String, nullable=False)
    blueprint_id = Column(Integer, nullable=True)
    purchase_price = Column(Float, nullable=False)
    rehab_cost = Column(Float, nullable=False)
    arv_estimate = Column(Float, nullable=False)
    rent_estimate = Column(Float, nullable=False)
    refinance_ltv = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PermitPackage(Base):
    __tablename__ = "permit_package"

    id = Column(Integer, primary_key=True, index=True)
    brrrr_id = Column(Integer, nullable=False)
    jurisdiction = Column(String, nullable=False)
    package_payload = Column(Text, nullable=False)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
