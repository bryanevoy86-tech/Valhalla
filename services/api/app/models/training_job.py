from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from app.models.base import Base


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String, nullable=False)
    target_module = Column(String, nullable=False)
    status = Column(String, default="pending")
    priority = Column(Integer, default=10)
    progress = Column(Float, default=0.0)
    payload = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)

__all__ = ["TrainingJob"]
