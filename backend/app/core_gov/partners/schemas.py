from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Type = Literal["jv_partner", "buyer", "lender", "contractor", "agent", "vendor", "other"]
Status = Literal["active", "paused", "archived"]
Tier = Literal["A", "B", "C", "D"]


class PartnerCreate(BaseModel):
    name: str
    partner_type: Type = "jv_partner"
    status: Status = "active"
    tier: Tier = "B"
    email: str = ""
    phone: str = ""
    location: str = ""                 # city/region/country
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class PartnerRecord(BaseModel):
    id: str
    name: str
    partner_type: Type
    status: Status
    tier: Tier
    email: str = ""
    phone: str = ""
    location: str = ""
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class PartnerListResponse(BaseModel):
    items: List[PartnerRecord]


class NoteCreate(BaseModel):
    partner_id: str
    title: str
    body: str = ""
    deal_id: str = ""
    visibility: Literal["internal", "shareable"] = "internal"
    meta: Dict[str, Any] = Field(default_factory=dict)


class DashboardResponse(BaseModel):
    totals: Dict[str, int] = Field(default_factory=dict)
    by_type: Dict[str, int] = Field(default_factory=dict)
    recent_partners: List[Dict[str, Any]] = Field(default_factory=list)
    recent_notes: List[Dict[str, Any]] = Field(default_factory=list)
