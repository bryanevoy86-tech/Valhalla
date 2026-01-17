"""PACK 83: Industry Engine - Cost Model
Cost structure and supply chain mapping.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime

from app.models.base import Base


class CostModel(Base):
    __tablename__ = "cost_model"

    id = Column(Integer, primary_key=True, index=True)
    product_line_id = Column(Integer, nullable=False)
    labor_cost = Column(Float, nullable=True)
    material_cost = Column(Float, nullable=True)
    overhead_cost = Column(Float, nullable=True)
    supply_chain_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
