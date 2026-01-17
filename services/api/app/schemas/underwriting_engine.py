# services/api/app/schemas/underwriting_engine.py

from __future__ import annotations

from decimal import Decimal
from typing import Dict, Optional

from pydantic import BaseModel, Field


class UnderwritingPolicyConfig(BaseModel):
    """
    Policy thresholds for underwriting decisions.
    These can later be loaded from DB or environment.
    """

    max_ltv: Decimal = Field(
        default=Decimal("0.80"),
        description="Maximum allowed loan-to-value ratio (e.g. 0.80 = 80%).",
    )
    min_roi: Decimal = Field(
        default=Decimal("0.12"),
        description="Minimum required return on investment (e.g. 0.12 = 12%).",
    )
    min_equity_percent: Decimal = Field(
        default=Decimal("0.10"),
        description="Minimum required equity as a fraction of ARV (e.g. 0.10 = 10%).",
    )
    strategy: str = Field(
        default="flip",
        description="Deal strategy (flip, brrrr, wholesale). Can adjust rules later.",
    )


class UnderwritingDealInput(BaseModel):
    """
    Deal numbers the engine uses to calculate underwriting metrics.
    """

    # Link to existing deal if available
    deal_id: Optional[int] = Field(
        default=None,
        description="Optional backend Deal.id this underwriting run is tied to.",
    )
    org_id: Optional[int] = Field(
        default=None,
        description="Optional organization id (for multi-tenant policies).",
    )

    arv: Decimal = Field(
        ...,
        description="After repair value estimate.",
    )
    purchase_price: Decimal = Field(
        ...,
        description="Price at which we expect to buy (offer price).",
    )
    repairs: Decimal = Field(
        default=Decimal("0"),
        description="Estimated repair / rehab budget.",
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
        description="Expected monthly rent (for BRRRR / hold scenarios).",
    )


class UnderwritingMetrics(BaseModel):
    """
    Calculated metrics.
    """

    total_project_cost: Decimal = Field(
        ...,
        description="Purchase + repairs + closing + holding costs.",
    )
    equity_amount: Decimal = Field(
        ...,
        description="ARV - total_project_cost.",
    )
    equity_percent_of_arv: Decimal = Field(
        ...,
        description="Equity / ARV.",
    )
    ltv: Decimal = Field(
        ...,
        description="Loan-to-value (purchase_price / ARV).",
    )
    roi: Decimal = Field(
        ...,
        description="Return on investment (equity / total_project_cost).",
    )
    holding_cost_total: Decimal = Field(
        ...,
        description="Total holding costs over the holding period.",
    )
    rent_coverage_ratio: Optional[Decimal] = Field(
        default=None,
        description="(expected_rent * 12) / (taxes + insurance + etc.), if available.",
    )


class UnderwritingFlags(BaseModel):
    """
    Policy violations and warnings.
    """

    breach_ltv: bool = False
    breach_roi: bool = False
    breach_equity: bool = False
    notes: str = ""


class UnderwritingResult(BaseModel):
    """
    Final decision result.
    """

    metrics: UnderwritingMetrics
    flags: UnderwritingFlags
    recommendation: str = Field(
        ...,
        description="Simple recommendation: offer, renegotiate, reject, review.",
    )
    policy: UnderwritingPolicyConfig
    debug: Dict[str, str] = Field(
        default_factory=dict,
        description="Optional debug information about calculations.",
    )


class UnderwriteDealRequest(BaseModel):
    deal: UnderwritingDealInput
    policy: Optional[UnderwritingPolicyConfig] = Field(
        default=None,
        description="Optional override of default underwriting policy.",
    )


class UnderwriteDealResponse(BaseModel):
    deal_id: Optional[int]
    org_id: Optional[int]
    result: UnderwritingResult
    freeze_event_created: bool = Field(
        default=False,
        description="True if an automated freeze_event was logged.",
    )
