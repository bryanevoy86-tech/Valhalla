from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ScheduledJobBase(BaseModel):
    name: str
    category: Optional[str] = "general"
    active: bool = True
    schedule: str
    task_path: str
    args: Optional[str] = None   # JSON string


class ScheduledJobCreate(ScheduledJobBase):
    pass


class ScheduledJobUpdate(BaseModel):
    name: Optional[str]
    category: Optional[str]
    active: Optional[bool]
    schedule: Optional[str]
    task_path: Optional[str]
    args: Optional[str]
    last_run_at: Optional[datetime]
    last_status: Optional[str]
    last_error: Optional[str]


class ScheduledJobOut(ScheduledJobBase):
    id: int
    last_run_at: Optional[datetime]
    last_status: Optional[str]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
