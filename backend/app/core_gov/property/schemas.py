from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Country = Literal["CA", "US"]


class PropertyCreate(BaseModel):
    country: Country = "CA"
    region: str = ""  # province/state code
    city: str = ""
    address: str = ""
    postal: str = ""
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    year_built: Optional[int] = None
    deal_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class PropertyRecord(BaseModel):
    id: str
    country: Country
    region: str
    city: str = ""
    address: str = ""
    postal: str = ""
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    year_built: Optional[int] = None
    deal_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class NeighborhoodRatingRequest(BaseModel):
    country: Country = "CA"
    region: str = ""
    city: str = ""
    address: str = ""
    postal: str = ""
    notes: str = ""


class NeighborhoodRatingResponse(BaseModel):
    score: float
    band: Literal["A", "B", "C", "D"]
    reasons: List[str] = Field(default_factory=list)
    placeholders: bool = True


class CompsRequest(BaseModel):
    property_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class CompsResponse(BaseModel):
    placeholders: bool = True
    suggested_arv: Optional[float] = None
    comps: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class RentRepairRequest(BaseModel):
    property_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class RentRepairResponse(BaseModel):
    placeholders: bool = True
    suggested_rent: Optional[float] = None
    repair_range: Dict[str, Any] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)


class PropertyListResponse(BaseModel):
    items: List[PropertyRecord]
