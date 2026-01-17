"""Governance Engine Schemas"""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PolicyRuleCreate(BaseModel):
    code: str
    description: str
    conditions: dict[str, Any]
    actions: dict[str, Any]
    enabled: bool = True


class PolicyRuleRead(BaseModel):
    id: UUID
    code: str
    description: str
    conditions: dict[str, Any]
    actions: dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PolicyRuleUpdate(BaseModel):
    description: Optional[str] = None
    conditions: Optional[dict[str, Any]] = None
    actions: Optional[dict[str, Any]] = None
    enabled: Optional[bool] = None
