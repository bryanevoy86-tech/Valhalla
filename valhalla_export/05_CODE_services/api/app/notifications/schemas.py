from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationCreate(BaseModel):
    user_id: str
    content: str


class Notification(BaseModel):
    user_id: str
    content: str
    timestamp: datetime
    is_read: bool = False

    class Config:
        from_attributes = True


class NotificationOut(BaseModel):
    user_id: str
    content: str
    timestamp: datetime
    is_read: bool

    class Config:
        from_attributes = True
