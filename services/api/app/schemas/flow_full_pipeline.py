# services/api/app/schemas/flow_full_pipeline.py

from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.flows_lead_to_deal import (
    LeadInput,
    LeadFlowResult,
    DealInput,
    DealFlowResult,
    BuyerMatchCandidate,
    BuyerMatchSettings,
)
from app.schemas.underwriting_engine import (
    UnderwritingPolicyConfig,
    UnderwritingResult,
)


class FullPipelineUnderwritingInput(BaseModel):
    """
    Underwriting details for the full pipeline.

    These are the numbers the underwriting engine needs.
    """

    arv: Decimal = Field(..., description="After repair value estimate.")
    purchase_price: Decimal = Field(
        ...,
        description="Offer / purchase price.",
    )
    repairs: Decimal = Field(
        default=Decimal("0"),
        description="Estimated rehab/repair budget.",
    )
    closing_costs: Decimal = Field(
        default=Decimal("0"),
        description="Closing costs (title, legal, lender fees, etc.).",
    )
    holding_months: int = Field(
        default=6,
        ge=0,
        description="Expected holding period in months.",
    )
    monthly_taxes: Decimal = Field(
        default=Decimal("0"),
        description="Monthly property taxes.",
    )
    monthly_insurance: Decimal = Field(
        default=Decimal("0"),
        description="Monthly property insurance.",
    )
    monthly_utilities: Decimal = Field(
        default=Decimal("0"),
        description="Monthly utilities during hold.",
    )
    monthly_hoa: Decimal = Field(
        default=Decimal("0"),
        description="Monthly HOA/condo fees.",
    )
    monthly_other: Decimal = Field(
        default=Decimal("0"),
        description="Other monthly holding costs.",
    )
    expected_rent: Optional[Decimal] = Field(
        default=None,
        description="Expected monthly rent (for BRRRR / hold deals).",
    )
    policy: Optional[UnderwritingPolicyConfig] = Field(
        default=None,
        description="Optional override of default underwriting policy.",
    )


class FullDealPipelineRequest(BaseModel):
    """
    One request that drives the entire deal pipeline:

    - lead: who / property
    - deal: marketing + basic numbers
    - match_settings: buyer matching behavior
    - underwriting: risk / policy numbers
    """

    lead: LeadInput
    deal: DealInput
    match_settings: BuyerMatchSettings = Field(
        default_factory=BuyerMatchSettings,
        description="Settings for buyer matching behavior.",
    )
    underwriting: FullPipelineUnderwritingInput


class FullDealPipelineResponse(BaseModel):
    """
    Unified response for the full pipeline:

    - lead (created)
    - deal (created DealBrief)
    - backend_deal_id (internal Deal row)
    - underwriting_result (metrics + recommendation)
    - matched_buyers
    - freeze_event_created (True if policy breach logged)
    - notes + metadata
    """

    lead: LeadFlowResult
    deal: DealFlowResult
    backend_deal_id: int
    underwriting_result: UnderwritingResult
    matched_buyers: List[BuyerMatchCandidate] = Field(
        default_factory=list,
        description="Buyer candidates that match this deal.",
    )
    freeze_event_created: bool = Field(
        default=False,
        description="True if a freeze_event was logged due to policy breach.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Summary of what happened and next-step hints.",
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Misc metadata (ids, thresholds, etc.).",
    )
