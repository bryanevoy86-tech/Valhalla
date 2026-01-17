"""PACK 85: Industry Engine - Regulatory & Licensing
Legal/licensing rules per industry and region.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models.base import Base


class IndustryRegulation(Base):
    __tablename__ = "industry_regulation"

    id = Column(Integer, primary_key=True, index=True)
    industry_id = Column(Integer, nullable=False)
    region = Column(String, nullable=False)
    requirements_payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
