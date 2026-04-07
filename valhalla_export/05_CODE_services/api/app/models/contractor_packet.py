"""PACK 70: Contractor Packet & Material Takeoff Engine
Generates contractor materials: takeoffs, diagrams, task lists.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models.base import Base


class ContractorPacket(Base):
    __tablename__ = "contractor_packet"

    id = Column(Integer, primary_key=True, index=True)
    blueprint_id = Column(Integer, nullable=False)
    material_list = Column(Text, nullable=False)
    task_breakdown = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
