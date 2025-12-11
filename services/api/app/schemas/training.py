"""PACK 88: Training Engine - Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TrainingModuleBase(BaseModel):
    title: str
    difficulty: str | None = None
    content_payload: str


class TrainingModuleCreate(TrainingModuleBase):
    pass


class TrainingModuleOut(TrainingModuleBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrainingProgressBase(BaseModel):
    user_id: int
    module_id: int
    completion_pct: float = 0.0
    status: str = "not_started"


class TrainingProgressCreate(TrainingProgressBase):
    pass


class TrainingProgressOut(TrainingProgressBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
