"""PACK 90: Health & Fitness Engine
Tracks health data, workouts, sleep, nutritional profiles.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime

from app.models.base import Base


class HealthMetric(Base):
    __tablename__ = "health_metric"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkoutSession(Base):
    __tablename__ = "workout_session"

    id = Column(Integer, primary_key=True, index=True)
    workout_type = Column(String, nullable=False)
    duration_minutes = Column(Float, nullable=False)
    intensity = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
