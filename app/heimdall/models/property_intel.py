from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer
from app.db.base import Base


class HeimdallPropertyIntel(Base):
    __tablename__ = "heimdall_property_intel"

    id = Column(String, primary_key=True, index=True)
    address = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False, index=True)
    province_or_state = Column(String, nullable=True, index=True)
    country = Column(String, nullable=True, index=True)

    research_status = Column(String, default="NEW", index=True)
    distress_score = Column(Integer, default=0, index=True)
    lead_lane = Column(String, default="UNSCORED", index=True)

    ownership_verified = Column(Boolean, default=False)
    outreach_allowed = Column(Boolean, default=False)
    converted_to_lead = Column(Boolean, default=False)

    raw_address_payload = Column(JSON, default=dict)
    property_data = Column(JSON, default=dict)
    research_plan = Column(JSON, default=dict)
    distress_analysis = Column(JSON, default=dict)
    notes = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
