from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AITrainingJobBase(BaseModel):
    engine_name: str
    job_type: str
    status: str = "queued"
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    dataset_label: Optional[str] = None
    epochs: int = 0
    loss_score: float = 0.0
    quality_score: float = 0.0
    error_message: Optional[str] = None
    notes: Optional[str] = None


class AITrainingJobCreate(AITrainingJobBase):
    pass


class AITrainingJobUpdate(BaseModel):
    status: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    epochs: Optional[int]
    loss_score: Optional[float]
    quality_score: Optional[float]
    error_message: Optional[str]
    notes: Optional[str]


class AITrainingJobOut(AITrainingJobBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
