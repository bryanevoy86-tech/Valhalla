from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


PropType = Literal["SFH", "duplex", "triplex", "condo", "apartment", "commercial", "land"]
Country = Literal["CA", "US"]


class PropertyIntelCreate(BaseModel):
    address: str
    city: str
    region: str
    postal: str
    country: Country = "CA"
    prop_type: PropType = "SFH"
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class PropertyIntelRecord(BaseModel):
    id: str
    address: str
    city: str
    region: str
    postal: str
    country: Country
    prop_type: PropType
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    arv_estimate: float = 0.0
    rent_estimate: float = 0.0
    repair_estimate: float = 0.0
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class CompCreate(BaseModel):
    property_intel_id: str
    address: str
    city: str
    region: str
    country: Country
    sold_price: float
    sold_date: str
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    distance_km: float = 0.0
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class CompRecord(BaseModel):
    id: str
    property_intel_id: str
    address: str
    city: str
    region: str
    country: Country
    sold_price: float
    sold_date: str
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    distance_km: float = 0.0
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class RepairLineCreate(BaseModel):
    property_intel_id: str
    item: str
    cost: float
    category: str = "other"
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class RepairLineRecord(BaseModel):
    id: str
    property_intel_id: str
    item: str
    cost: float
    category: str
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class PropertyListResponse(BaseModel):
    items: List[PropertyIntelRecord]


class CompListResponse(BaseModel):
    items: List[CompRecord]


class RepairListResponse(BaseModel):
    items: List[RepairLineRecord]


class IntelSummaryResponse(BaseModel):
    property_id: str
    address: str
    country: Country
    comps_count: int = 0
    repairs_count: int = 0
    total_repair_cost: float = 0.0
    avg_comp_price: float = 0.0
    arv_estimate: float = 0.0
    rent_estimate: float = 0.0
