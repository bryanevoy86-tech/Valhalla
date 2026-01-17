"""PACK 63: Evolution Engine
Event logging for system evolution and adaptation triggers.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from app.models.base import Base


class EvolutionEvent(Base):
    __tablename__ = "evolution_event"

    id = Column(Integer, primary_key=True, index=True)
    trigger = Column(String, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
