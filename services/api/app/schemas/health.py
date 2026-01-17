"""PACK 90: Health & Fitness - Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HealthMetricBase(BaseModel):
    metric_name: str
    value: float
    notes: str | None = None


class HealthMetricCreate(HealthMetricBase):
    pass


class HealthMetricOut(HealthMetricBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkoutSessionBase(BaseModel):
    workout_type: str
    duration_minutes: float
    intensity: str | None = None
    notes: str | None = None


class WorkoutSessionCreate(WorkoutSessionBase):
    pass


class WorkoutSessionOut(WorkoutSessionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
