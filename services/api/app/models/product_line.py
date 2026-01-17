"""PACK 82: Industry Engine - Product Line Models
Product catalogs for industries.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float

from app.models.base import Base


class ProductLine(Base):
    __tablename__ = "product_line"

    id = Column(Integer, primary_key=True, index=True)
    industry_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    cost_structure = Column(Text, nullable=True)
    retail_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
