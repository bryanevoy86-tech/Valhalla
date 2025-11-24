from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SystemHealthBase(BaseModel):
    service_name: str
    status: Optional[str] = "unknown"
    notes: Optional[str] = None


class SystemHealthCreate(SystemHealthBase):
    pass


class SystemHealthUpdate(BaseModel):
    status: Optional[str]
    notes: Optional[str]
    issue_count: Optional[int]
    last_heartbeat: Optional[datetime]


class SystemHealthOut(SystemHealthBase):
    id: int
    last_heartbeat: Optional[datetime]
    issue_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
