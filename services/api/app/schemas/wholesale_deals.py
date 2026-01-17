"""
PACK SJ: Wholesale Deal Machine
Pydantic schemas for wholesale workflow
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class WholesaleLeadSchema(BaseModel):
    lead_id: str = Field(..., description="Unique lead identifier")
    source: str = Field(..., description="Lead source (website, ad, referral, cold-call)")
    seller_name: Optional[str] = None
    seller_contact: Optional[str] = None
    property_address: str = Field(..., description="Property address")
    motivation_level: Optional[str] = Field(None, description="User-scored motivation")
    situation_notes: Optional[str] = None
    stage: str = Field("new", description="Deal stage")

    class Config:
        from_attributes = True


class WholesaleOfferSchema(BaseModel):
    offer_id: str = Field(..., description="Unique offer identifier")
    lead_id: int
    offer_price: int = Field(..., description="Offer price in cents")
    arv: Optional[int] = Field(None, description="After-repair value in cents")
    repair_estimate: Optional[int] = Field(None, description="Repair estimate in cents")
    notes: Optional[str] = None
    status: str = Field("draft", description="Offer status")

    class Config:
        from_attributes = True


class BuyerProfileSchema(BaseModel):
    buyer_id: str = Field(..., description="Unique buyer identifier")
    name: str = Field(..., description="Buyer name")
    contact: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = Field(None, description="Buyer preferences")
    notes: Optional[str] = None
    status: str = Field("active", description="Buyer status")

    class Config:
        from_attributes = True


class AssignmentRecordSchema(BaseModel):
    assignment_id: str = Field(..., description="Unique assignment identifier")
    lead_id: int
    buyer_id: Optional[int] = None
    buyer_name: Optional[str] = None
    buyer_contact: Optional[str] = None
    assignment_fee: int = Field(..., description="Fee in cents")
    notes: Optional[str] = None
    status: str = Field("draft", description="Assignment status")

    class Config:
        from_attributes = True


class WholesalePipelineSnapshotSchema(BaseModel):
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    date: datetime
    total_leads: int
    by_stage: Optional[Dict[str, int]] = None
    hot_leads: int = Field(0, description="High-motivation leads")
    active_offers: int = Field(0)
    ready_for_assignment: int = Field(0)
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class DealPipelineResponse(BaseModel):
    total_leads: int
    new: int
    contacted: int
    inspection: int
    offer_sent: int
    negotiating: int
    contract_signed: int
    assigned: int
    closed: int
