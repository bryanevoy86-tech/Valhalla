"""
Pydantic schemas for messaging (email/SMS) and templates.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class EmailTemplateCreate(BaseModel):
    template_name: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)

class EmailTemplateOut(BaseModel):
    template_id: int
    template_name: str
    subject: str
    body: str
    created_at: datetime

    class Config:
        from_attributes = True

class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    html: bool = False

class SendSmsRequest(BaseModel):
    to: str
    message: str

class SendWithTemplateRequest(BaseModel):
    template_name: str
    to: Optional[str] = None
    user_id: Optional[int] = None
    variables: Dict[str, Any] = {}

class NotifyUserRequest(BaseModel):
    user_id: int
    subject: str
    body: str
    sms_message: Optional[str] = None
