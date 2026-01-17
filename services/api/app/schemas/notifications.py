from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationBase(BaseModel):
    channel: Optional[str] = "system"
    audience: Optional[str] = "king"
    title: str
    message: str
    severity: Optional[str] = "info"


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    read: Optional[bool]
    read_at: Optional[datetime]


class NotificationOut(NotificationBase):
    id: int
    read: bool
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        orm_mode = True
