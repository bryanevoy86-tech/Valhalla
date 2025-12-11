"""PACK 71: Renovation Cost Simulator
Runs cost simulations for materials, labor, timeline, and ROI.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text

from app.models.base import Base


class RenoCostSimulation(Base):
    __tablename__ = "reno_cost_simulation"

    id = Column(Integer, primary_key=True, index=True)
    blueprint_id = Column(Integer, nullable=False)
    input_payload = Column(Text, nullable=False)
    low_estimate = Column(Float, nullable=False)
    mid_estimate = Column(Float, nullable=False)
    high_estimate = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
