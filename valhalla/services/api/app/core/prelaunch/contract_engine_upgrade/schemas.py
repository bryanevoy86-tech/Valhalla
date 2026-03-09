"""Contract Engine Upgrade Schemas"""
from datetime import datetime
from typing import Optional, Any, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ContractTemplateCreate(BaseModel):
    name: str
    category: str
    language: str = "en"
    body: str
    template_metadata: Optional[dict[str, Any]] = None


class ContractTemplateRead(BaseModel):
    id: UUID
    name: str
    category: str
    language: str
    body: str
    template_metadata: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContractReviewRequest(BaseModel):
    source: str
    category: Optional[str] = None
    text: str


class ContractReviewRead(BaseModel):
    id: UUID
    source: str
    category: Optional[str] = None
    text: str
    red_flags: Optional[list[dict[str, Any]]] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
