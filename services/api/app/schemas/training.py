from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TrainingJobBase(BaseModel):
    job_type: str
    target_module: str
    priority: int = 10
    payload: Optional[str] = None


class TrainingJobCreate(TrainingJobBase):
    pass


class TrainingJobUpdate(BaseModel):
    status: Optional[str]
    priority: Optional[int]
    progress: Optional[float]
    payload: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


class TrainingJobOut(TrainingJobBase):
    id: int
    status: str
    progress: float
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    class Config:
        orm_mode = True
