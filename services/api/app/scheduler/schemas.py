from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobBase(BaseModel):
    name: str
    description: Optional[str] = None
    cron_expr: str
    active: bool = True


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    last_run: Optional[datetime] = None

    class Config:
        from_attributes = True
