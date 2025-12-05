# services/api/app/schemas/closing_context.py

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.flows_lead_to_deal import BuyerMatchCandidate
from app.schemas.underwriting_engine import UnderwritingResult


class LeadSummary(BaseModel):
    id: int
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    address: Optional[str] = None
    tags: Optional[str] = None


class DealSummary(BaseModel):
    backend_deal_id: int
    deal_brief_id: Optional[int] = None
    status: str
    headline: Optional[str] = None
    region: Optional[str] = None
    property_type: Optional[str] = None
    price: Optional[Decimal] = None
    arv: Optional[Decimal] = None
    repairs: Optional[Decimal] = None
    offer: Optional[Decimal] = None
    mao: Optional[Decimal] = None
    notes: Optional[str] = None


class FreezeSummary(BaseModel):
    has_freeze: bool = False
    severity: Optional[str] = None
    reason: Optional[str] = None
    count: int = 0


class UnderwritingSummary(BaseModel):
    """
    High-level underwriting snapshot used for closing context.

    We embed the UnderwritingResult if available, but keep a flat summary
    here so the closer logic can work off basic numbers even if the full
    engine wasn't run recently.
    """

    recommendation: Optional[str] = None
    ltv: Optional[Decimal] = None
    roi: Optional[Decimal] = None
    equity_percent_of_arv: Optional[Decimal] = None
    notes: Optional[str] = None
    raw: Optional[UnderwritingResult] = None


class ClosingContext(BaseModel):
    """
    What the closer engine / Heimdall needs to know before starting a
    closing / negotiation conversation.
    """

    lead: LeadSummary
    deal: DealSummary
    buyers: List[BuyerMatchCandidate] = Field(
        default_factory=list,
        description="Top buyer candidates for this deal.",
    )
    freeze: FreezeSummary
    underwriting: UnderwritingSummary
    suggested_opening: str = Field(
        ...,
        description="Suggested first line / opening script for the closer.",
    )
