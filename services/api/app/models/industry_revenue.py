"""PACK 84: Industry Engine - Revenue Simulator
Revenue projections for new business lines.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime

from app.models.base import Base


class IndustryRevenueSim(Base):
    __tablename__ = "industry_revenue_sim"

    id = Column(Integer, primary_key=True, index=True)
    industry_id = Column(Integer, nullable=False)
    assumptions_payload = Column(Text, nullable=False)
    low_estimate = Column(Float, nullable=False)
    mid_estimate = Column(Float, nullable=False)
    high_estimate = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
