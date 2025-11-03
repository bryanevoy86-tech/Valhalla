"""
Schemas for lead intake and normalization.
"""

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Any, Dict


class LeadIn(BaseModel):
    source: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    property_type: Optional[str] = None
    price: Optional[float] = None
    beds: Optional[int] = None
    baths: Optional[int] = None
    notes: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None  # original payload if any


class LeadOut(LeadIn):
    id: int
    status: str
    deal_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class NormalizeOut(BaseModel):
    ok: bool
    lead_id: int
    deal_id: Optional[int] = None
