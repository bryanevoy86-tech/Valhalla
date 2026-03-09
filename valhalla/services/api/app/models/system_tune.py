"""
PACK TF: System Tune List Models
Master checklist of everything to verify, tune, or improve.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.core.db import Base


class TuneArea(Base):
    __tablename__ = "tune_areas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Backend, Frontend, Heimdall, Finance, etc.
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<TuneArea(name={self.name})>"


class TuneItem(Base):
    __tablename__ = "tune_items"

    id = Column(Integer, primary_key=True, index=True)
    area_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, nullable=True)  # 1–5
    status = Column(String, default="pending")  # pending, in_progress, done, skipped
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<TuneItem(title={self.title}, status={self.status})>"
