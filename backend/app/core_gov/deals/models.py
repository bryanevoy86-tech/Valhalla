from __future__ import annotations

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class DealIn(BaseModel):
    # identity / location
    country: str = Field(..., description="CA or US")
    province_state: str = Field(..., description="Province (CA) or State (US), e.g., MB, ON, FL, TX")
    city: str
    address: Optional[str] = None
    postal_zip: Optional[str] = None

    # deal type
    strategy: str = Field(..., description="wholesale|brrrr|flip|rental")
    property_type: str = Field(default="sfh", description="sfh|duplex|triplex|fourplex|condo|townhouse|land|small_mf")
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None

    # financials (currency depends on country)
    arv: Optional[float] = None
    asking_price: Optional[float] = None
    est_repairs: Optional[float] = None
    mao: Optional[float] = None  # max allowable offer
    est_rent_monthly: Optional[float] = None

    # seller / motivation
    seller_motivation: str = Field(default="unknown", description="high|medium|low|unknown")
    seller_reason: Optional[str] = None  # divorce, inherited, tired landlord, job loss, etc.
    timeline_days: Optional[int] = None

    # pipeline
    stage: str = Field(default="new", description="new|contacted|qualified|offer_sent|negotiating|under_contract|dead|closed")
    lead_source: str = Field(default="seed", description="seed|public|real")
    tags: List[str] = []
    notes: Optional[str] = None

    # arbitrary metadata
    meta: Dict[str, Any] = {}

class Deal(DealIn):
    id: str
    created_at_utc: str
    updated_at_utc: str
