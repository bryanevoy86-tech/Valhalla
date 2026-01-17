"""
PACK UG: Notification & Alert Channel Engine Schemas
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel


class NotificationChannelCreate(BaseModel):
    name: str
    channel_type: str
    target: str
    active: bool = True
    description: Optional[str] = None


class NotificationChannelOut(NotificationChannelCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationChannelList(BaseModel):
    total: int
    items: List[NotificationChannelOut]


class NotificationCreate(BaseModel):
    channel_id: int
    subject: Optional[str] = None
    body: str
    payload: Optional[Dict[str, Any]] = None


class NotificationOut(NotificationCreate):
    id: int
    created_at: datetime
    status: str
    last_error: Optional[str]
    attempts: int

    class Config:
        from_attributes = True


class NotificationList(BaseModel):
    total: int
    items: List[NotificationOut]
