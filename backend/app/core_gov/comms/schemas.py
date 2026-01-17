from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Channel = Literal["sms", "email", "call", "dm", "letter", "other"]
Status = Literal["draft", "queued", "sent", "canceled"]
Tone = Literal["neutral", "warm", "firm", "urgent"]


class MessageCreate(BaseModel):
    title: str
    channel: Channel = "email"
    status: Status = "draft"
    tone: Tone = "neutral"
    to: str = ""                       # phone/email/handle
    subject: str = ""
    body: str = ""
    deal_id: str = ""
    contact_id: str = ""
    partner_id: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class MessageRecord(BaseModel):
    id: str
    title: str
    channel: Channel
    status: Status
    tone: Tone
    to: str = ""
    subject: str = ""
    body: str = ""
    deal_id: str = ""
    contact_id: str = ""
    partner_id: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    sent_at: str = ""
    created_at: datetime
    updated_at: datetime


class MessageListResponse(BaseModel):
    items: List[MessageRecord]


class MarkSentRequest(BaseModel):
    sent_at: str = ""                  # ISO optional
    meta: Dict[str, Any] = Field(default_factory=dict)
