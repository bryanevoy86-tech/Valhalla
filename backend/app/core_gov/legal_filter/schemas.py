from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Severity = Literal["info", "low", "medium", "high"]
Outcome = Literal["allowed", "flagged", "blocked"]


class JurisdictionProfileUpsert(BaseModel):
    key: str                          # "CA:MB" or "US:FL"
    name: str = ""                    # "Manitoba" / "Florida"
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class JurisdictionProfileRecord(BaseModel):
    key: str
    name: str = ""
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ProfileListResponse(BaseModel):
    items: List[JurisdictionProfileRecord]


class LegalCheckRequest(BaseModel):
    jurisdiction_key: str             # "CA:MB"
    subject: str = "deal"             # deal/contract/offer/etc
    payload: Dict[str, Any] = Field(default_factory=dict)
    mode: str = "execute"             # explore/execute (mode-safe)
    cone_band: str = "B"              # A-D (optional)
    meta: Dict[str, Any] = Field(default_factory=dict)


class LegalFinding(BaseModel):
    rule_id: str
    outcome: Outcome
    severity: Severity
    message: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    next_actions: List[str] = Field(default_factory=list)


class LegalCheckResponse(BaseModel):
    jurisdiction_key: str
    subject: str
    overall: Outcome
    findings: List[LegalFinding] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
