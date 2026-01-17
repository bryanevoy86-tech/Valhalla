"""PACK 81: Industry Engine - Registry Models
Industry profile templates and configurations.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

from app.models.base import Base


class IndustryProfile(Base):
    __tablename__ = "industry_profile"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    config_payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
