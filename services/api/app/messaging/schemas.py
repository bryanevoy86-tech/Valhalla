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
    # Market policy enforcement (optional)
    province: Optional[str] = None
    market: Optional[str] = None
    weekday: Optional[int] = None  # 0=Monday, 6=Sunday
    hhmm: Optional[str] = None  # "HHMM" format e.g. "0900" for 9 AM

class SendSmsRequest(BaseModel):
    to: str
    message: str
    # Market policy enforcement (optional)
    province: Optional[str] = None
    market: Optional[str] = None
    weekday: Optional[int] = None  # 0=Monday, 6=Sunday
    hhmm: Optional[str] = None  # "HHMM" format e.g. "0900" for 9 AM

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
