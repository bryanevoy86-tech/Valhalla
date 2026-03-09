"""
PACK CI2: Opportunity Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Boolean
from app.models.base import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String, nullable=False)   # "deal", "shipwreck", "grant", "content", etc.
    source_id = Column(String, nullable=True)      # optional external ID
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Scores
    value_score = Column(Float, nullable=False, default=0.0)
    effort_score = Column(Float, nullable=False, default=0.0)
    risk_score = Column(Float, nullable=False, default=0.0)
    roi_score = Column(Float, nullable=False, default=0.0)
    time_horizon_days = Column(Integer, nullable=True)

    # Meta
    tags = Column(JSON, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
