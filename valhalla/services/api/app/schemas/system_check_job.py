from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SystemCheckJobBase(BaseModel):
    name: str
    scope: str
    scope_code: Optional[str] = None
    schedule: str = "weekly"
    active: bool = True
    notes: Optional[str] = None


class SystemCheckJobCreate(SystemCheckJobBase):
    pass


class SystemCheckJobUpdate(BaseModel):
    schedule: Optional[str]
    active: Optional[bool]
    last_run_at: Optional[datetime]
    last_status: Optional[str]
    last_health_score: Optional[float]
    notes: Optional[str]


class SystemCheckJobOut(SystemCheckJobBase):
    id: int
    last_run_at: Optional[datetime]
    last_status: Optional[str]
    last_health_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
