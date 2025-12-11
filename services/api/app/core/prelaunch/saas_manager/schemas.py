"""SaaS Manager Schemas"""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TenantCreate(BaseModel):
    name: str
    contact_email: str
    plan: str = "STARTER"
    status: str = "TRIAL"


class TenantRead(BaseModel):
    id: UUID
    name: str
    contact_email: str
    plan: str
    status: str
    usage: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantUpdate(BaseModel):
    plan: Optional[str] = None
    status: Optional[str] = None
    usage: Optional[dict[str, Any]] = None
