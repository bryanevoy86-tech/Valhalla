"""PACK-CORE-PRELAUNCH-01: Scenarios Engine - Schemas"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .models import ScenarioCategory, ScenarioSeverity


class ScenarioBase(BaseModel):
    code: str
    category: ScenarioCategory
    severity: ScenarioSeverity
    name: str
    description: Optional[str] = None
    trigger_conditions: Optional[dict[str, Any]] = None
    recommended_actions: Optional[list[dict[str, Any]]] = None
    fallback_actions: Optional[list[dict[str, Any]]] = None
    auto_actions: Optional[list[dict[str, Any]]] = None
    enabled: bool = True


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[ScenarioSeverity] = None
    trigger_conditions: Optional[dict[str, Any]] = None
    recommended_actions: Optional[list[dict[str, Any]]] = None
    fallback_actions: Optional[list[dict[str, Any]]] = None
    auto_actions: Optional[list[dict[str, Any]]] = None
    enabled: Optional[bool] = None


class ScenarioRead(ScenarioBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
