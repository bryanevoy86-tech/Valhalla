"""
PACK AJ: Notification Bridge Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class NotificationPreferenceCreate(BaseModel):
    user_id: int
    entity_type: Optional[str] = Field(
        None, description="deal, property, child, etc. Leave None for all entities"
    )
    event_type: str = Field(..., description="event type key, e.g. 'deal_status_changed'")
    channel_key: str = Field(..., description="email, sms, in_app, etc.")
    template_key: str = Field(..., description="notification template key")


class NotificationPreferenceUpdate(BaseModel):
    entity_type: Optional[str] = None
    event_type: Optional[str] = None
    channel_key: Optional[str] = None
    template_key: Optional[str] = None
    is_enabled: Optional[bool] = None


class NotificationPreferenceOut(BaseModel):
    id: int
    user_id: int
    entity_type: Optional[str]
    event_type: str
    channel_key: str
    template_key: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BridgeDispatchResult(BaseModel):
    """
    Summary of notifications triggered from a single event.
    """
    event_id: int
    notifications_created: int
    recipients: list[int]
