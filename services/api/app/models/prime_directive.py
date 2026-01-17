"""PACK 61: Prime Directive Engine
Core directive storage and retrieval mechanism.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from app.models.base import Base


class PrimeDirective(Base):
    __tablename__ = "prime_directive"

    id = Column(Integer, primary_key=True, index=True)
    directive = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
