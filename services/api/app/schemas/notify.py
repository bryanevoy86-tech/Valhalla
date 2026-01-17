"""
Schemas for notification queueing (webhooks, emails).
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, Any, Dict


class WebhookQueueIn(BaseModel):
    url: Optional[str] = None      # if omitted, use DEFAULT_WEBHOOK_URL
    payload: Dict[str, Any]


class EmailQueueIn(BaseModel):
    to: EmailStr
    subject: str
    body_text: str
