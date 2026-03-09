"""PACK 88: Employee / VA Training Engine
Creates training modules, tracks progress, certifies skills.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float

from app.models.base import Base


class TrainingModule(Base):
    __tablename__ = "training_module"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    difficulty = Column(String, nullable=True)
    content_payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrainingProgress(Base):
    __tablename__ = "training_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    module_id = Column(Integer, nullable=False)
    completion_pct = Column(Float, default=0.0)
    status = Column(String, default="not_started")
    created_at = Column(DateTime, default=datetime.utcnow)
