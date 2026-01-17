from sqlalchemy import Column, Integer, String, Float, DateTime, Text
import datetime
from app.db.base_class import Base


class AITrainingJob(Base):
    __tablename__ = "ai_training_jobs"

    id = Column(Integer, primary_key=True, index=True)
    engine_name = Column(String, nullable=False)
    job_type = Column(String, nullable=False)
    status = Column(String, default="queued")
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    dataset_label = Column(String)
    epochs = Column(Integer, default=0)
    loss_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    error_message = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
