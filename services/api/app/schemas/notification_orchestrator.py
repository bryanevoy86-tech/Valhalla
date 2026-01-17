"""
PACK AG: Notification Orchestrator Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class NotificationChannelCreate(BaseModel):
    key: str = Field(..., description="email, sms, in_app, push, etc.")
    name: str
    description: Optional[str] = None


class NotificationChannelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class NotificationChannelOut(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationTemplateCreate(BaseModel):
    key: str = Field(..., description="template identifier, e.g. 'deal_status_update'")
    channel_key: str
    subject: Optional[str] = None
    body: str
    description: Optional[str] = None


class NotificationTemplateUpdate(BaseModel):
    channel_key: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class NotificationTemplateOut(BaseModel):
    id: int
    key: str
    channel_key: str
    subject: Optional[str]
    body: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationSendRequest(BaseModel):
    template_key: str
    channel_override: Optional[str] = Field(
        None,
        description="Optional override of channel_key"
    )
    recipient: str
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Placeholder values for template (e.g. {'deal_id': 123})",
    )


class NotificationLogOut(BaseModel):
    id: int
    channel_key: str
    template_key: Optional[str]
    recipient: str
    subject: Optional[str]
    body: str
    status: str
    error_message: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True
