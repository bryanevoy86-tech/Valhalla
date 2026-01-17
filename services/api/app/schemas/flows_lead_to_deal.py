# services/api/app/schemas/flows_lead_to_deal.py

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Lead ----------


class LeadInput(BaseModel):
    """
    Lead payload for the lead → deal flow.

    This intentionally merges fields from:
    - Pack 31 Lead (name, email, phone, source)
    - Backend lead/deal (address, tags, owner/org context)
    """

    name: str = Field(..., max_length=200, description="Full name of the seller/lead.")
    email: Optional[EmailStr] = Field(
        default=None, description="Email address of the lead."
    )
    phone: Optional[str] = Field(
        default=None, max_length=50, description="Phone number of the lead."
    )
    source: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Lead source (Facebook, referral, LinkedIn, etc.).",
    )
    address: Optional[str] = Field(
        default=None,
        description="Property address associated with this lead.",
    )
    tags: Optional[str] = Field(
        default=None,
        description="Optional free-form tags or labels for the lead.",
    )
    org_id: Optional[int] = Field(
        default=None,
        description="Optional org/portfolio id if multi-tenant.",
    )


class LeadFlowResult(BaseModel):
    id: int
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: Optional[str] = None


# ---------- Deal ----------


class DealInput(BaseModel):
    """
    Deal payload that merges:

    - DealBrief (match system)
    - Backend Deal financials (arv, repairs, offer, mao, roi_note)
    """

    headline: str = Field(
        ...,
        max_length=240,
        description="Short marketing headline for the deal.",
    )
    region: Optional[str] = Field(
        default=None, max_length=120, description="Market/region name."
    )
    property_type: Optional[str] = Field(
        default=None,
        max_length=40,
        description="Property type (SFH, Duplex, Triplex, etc.).",
    )
    price: Optional[Decimal] = Field(
        default=None,
        description="Asking price or expected purchase price.",
    )
    beds: Optional[int] = Field(
        default=None,
        description="Bedroom count.",
        ge=0,
    )
    baths: Optional[int] = Field(
        default=None,
        description="Bathroom count.",
        ge=0,
    )
    notes: Optional[str] = Field(
        default=None,
        description="Free-form notes for internal use.",
    )
    status: str = Field(
        default="active",
        description="Deal status (active, under_contract, sold, archived).",
    )

    # Financials (backend Deal)
    arv: Optional[Decimal] = Field(
        default=None,
        description="After repair value estimate.",
    )
    repairs: Optional[Decimal] = Field(
        default=None,
        description="Estimated repair costs.",
    )
    offer: Optional[Decimal] = Field(
        default=None,
        description="Current or intended offer price.",
    )
    mao: Optional[Decimal] = Field(
        default=None,
        description="Maximum allowable offer.",
    )
    roi_note: Optional[str] = Field(
        default=None,
        description="Notes about ROI / underwriting rationale.",
    )


class DealFlowResult(BaseModel):
    id: int
    headline: str
    region: Optional[str] = None
    property_type: Optional[str] = None
    price: Optional[Decimal] = None
    status: str


# ---------- Buyer Match ----------


class BuyerMatchCandidate(BaseModel):
    buyer_id: int
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Match score between 0 and 1.",
    )
    reasons: List[str] = Field(
        default_factory=list,
        description="List of reasons why this buyer matched.",
    )
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class BuyerMatchSettings(BaseModel):
    match_buyers: bool = Field(
        default=True,
        description="Whether to attempt buyer matching as part of the flow.",
    )
    min_match_score: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum score (0–1) to consider a buyer a match.",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of buyer candidates to return.",
    )


# ---------- Flow request / response ----------


class LeadToDealRequest(BaseModel):
    """
    Single request body for the lead → deal flow.
    """

    lead: LeadInput
    deal: DealInput
    match_settings: BuyerMatchSettings = Field(
        default_factory=BuyerMatchSettings,
        description="Settings for buyer matching behavior.",
    )


class LeadToDealResponse(BaseModel):
    """
    Unified response for the flow:
    - Created lead
    - Created deal brief (match system)
    - Optional buyer matches
    """

    lead: LeadFlowResult
    deal: DealFlowResult
    matched_buyers: List[BuyerMatchCandidate] = Field(
        default_factory=list,
        description="Buyer candidates that match this deal.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Any additional commentary or next steps.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional misc metadata (timings, scoring params, etc.).",
    )
