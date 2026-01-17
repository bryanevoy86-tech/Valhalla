"""PACK 93: Multi-Zone Expansion - Models"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models.base import Base


class BusinessZone(Base):
    __tablename__ = "business_zone"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)        # e.g. "Ontario", "BC", "Texas"
    region_code = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
