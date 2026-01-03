from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class JurisdictionProfile(BaseModel):
    id: str
    country: Literal["CA", "US"]
    region: str  # MB, ON, FL, TX, etc.
    name: str  # Display name
    notes: str = Field(default="")
    created_at: datetime
    updated_at: datetime


class RuleCondition(BaseModel):
    field: str
    op: Literal["eq", "neq", "in", "nin", "exists", "truthy", "falsy", "contains"]
    value: Optional[Any] = Field(default=None)


class LegalRule(BaseModel):
    id: str
    name: str
    description: str = Field(default="")
    country: Literal["CA", "US"]
    region: str
    severity: Literal["info", "warn", "block"]
    conditions: List[RuleCondition] = Field(default_factory=list)
    action_hint: str = Field(default="")
    created_at: datetime
    updated_at: datetime


class Flag(BaseModel):
    rule_id: str
    name: str
    severity: Literal["info", "warn", "block"]
    reason: str
    action_hint: str = Field(default="")


class EvaluateResponse(BaseModel):
    ok: bool
    country: str
    region: str
    flags: List[Flag] = Field(default_factory=list)
    blocked: bool
    summary: str = Field(default="")


class JurisdictionListResponse(BaseModel):
    items: List[JurisdictionProfile]


class RuleListResponse(BaseModel):
    items: List[LegalRule]
