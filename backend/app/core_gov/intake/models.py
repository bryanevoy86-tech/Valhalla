from __future__ import annotations

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class LeadIn(BaseModel):
    source: str = Field(..., description="Where it came from (call, text, web, referral, etc.)")
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = "CA"
    notes: Optional[str] = None
    tags: list[str] = []
    meta: Dict[str, Any] = {}

class Lead(LeadIn):
    id: str
    created_at_utc: str
