"""Negotiation Engine Schemas"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class NegotiationTemplateBase(BaseModel):
    category: str
    tone_profile: str
    script: dict[str, Any]


class NegotiationTemplateCreate(NegotiationTemplateBase):
    pass


class NegotiationTemplateRead(NegotiationTemplateBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NegotiationRequest(BaseModel):
    target_name: Optional[str] = None
    category: str
    tone_profile: Optional[str] = None
    context: Optional[dict[str, Any]] = None


class NegotiationResponse(BaseModel):
    output: str
    style_used: str
