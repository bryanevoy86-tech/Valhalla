"""PACK-CORE-PRELAUNCH-01: Safeguard Matrix - Schemas"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .models import SafeguardCategory, SafeguardDomain


class SafeguardRuleBase(BaseModel):
    name: str
    category: SafeguardCategory
    domain: SafeguardDomain
    condition_definition: Optional[dict[str, Any]] = None
    effect_definition: Optional[dict[str, Any]] = None
    enabled: bool = True


class SafeguardRuleCreate(SafeguardRuleBase):
    pass


class SafeguardRuleUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[SafeguardCategory] = None
    domain: Optional[SafeguardDomain] = None
    condition_definition: Optional[dict[str, Any]] = None
    effect_definition: Optional[dict[str, Any]] = None
    enabled: Optional[bool] = None


class SafeguardRuleRead(SafeguardRuleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
