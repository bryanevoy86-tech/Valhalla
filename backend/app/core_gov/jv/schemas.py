from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


PartnerType = Literal["buyer", "lender", "jv", "vendor", "agent", "other"]
PartnerStatus = Literal["active", "paused", "blocked"]


class PartnerCreate(BaseModel):
    name: str
    partner_type: PartnerType = "jv"
    status: PartnerStatus = "active"
    email: str = ""
    phone: str = ""
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class PartnerRecord(BaseModel):
    id: str
    name: str
    partner_type: PartnerType
    status: PartnerStatus
    email: str = ""
    phone: str = ""
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class DealLink(BaseModel):
    partner_id: str
    deal_id: str
    role: str = "jv"
    split: str = ""  # "50/50" etc
    notes: str = ""
    created_at: datetime


class DashboardResponse(BaseModel):
    partner: PartnerRecord
    deals: List[DealLink] = Field(default_factory=list)
    computed: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class PartnerListResponse(BaseModel):
    items: List[PartnerRecord]
