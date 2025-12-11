"""Family OS Schemas"""
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class FamilyValuesRead(BaseModel):
    id: UUID
    mission: Optional[str] = None
    core_values: Optional[List[str]] = None
    rules: Optional[list[dict[str, Any]]] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FamilyValuesUpdate(BaseModel):
    mission: Optional[str] = None
    core_values: Optional[List[str]] = None
    rules: Optional[list[dict[str, Any]]] = None


class FamilyRoutineRead(BaseModel):
    id: UUID
    name: str
    steps: Optional[list[dict[str, Any]]] = None
    category: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FamilyRoutineCreate(BaseModel):
    name: str
    steps: Optional[list[dict[str, Any]]] = None
    category: Optional[str] = None


class FamilyRoutineUpdate(BaseModel):
    name: Optional[str] = None
    steps: Optional[list[dict[str, Any]]] = None
    category: Optional[str] = None


class ScreenTimeRuleRead(BaseModel):
    id: UUID
    age_group: str
    max_minutes_per_day: str
    allowed_categories: Optional[list[str]] = None
    blocked_categories: Optional[list[str]] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScreenTimeRuleCreate(BaseModel):
    age_group: str
    max_minutes_per_day: str
    allowed_categories: Optional[list[str]] = None
    blocked_categories: Optional[list[str]] = None


class ScreenTimeRuleUpdate(BaseModel):
    max_minutes_per_day: Optional[str] = None
    allowed_categories: Optional[list[str]] = None
    blocked_categories: Optional[list[str]] = None
