"""PACK 65: Auto-Scaling Clone Engine
Replicates systems for new regions, markets, or business units.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from app.models.base import Base


class CloneProfile(Base):
    __tablename__ = "clone_profiles"

    id = Column(Integer, primary_key=True, index=True)
    source_zone = Column(String, nullable=False)
    target_zone = Column(String, nullable=False)
    status = Column(String, default="pending")
    include_modules = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
