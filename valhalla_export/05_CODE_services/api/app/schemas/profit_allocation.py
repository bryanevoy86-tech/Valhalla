# services/api/app/schemas/profit_allocation.py

from __future__ import annotations

from decimal import Decimal
from typing import Dict, Optional

from pydantic import BaseModel, Field


class ProfitAllocationPolicy(BaseModel):
    """
    Policy thresholds around how profit is allocated.

    This is where your Valhalla "rules" live for tax, FunFunds, and reinvestment.
    """

    min_tax_rate: Decimal = Field(
        default=Decimal("0.20"),
        description="Minimum effective tax rate (e.g. 0.20 = 20%).",
    )
    max_funfunds_percent: Decimal = Field(
        default=Decimal("0.25"),
        description="Maximum share of post-tax profit that can go to FunFunds.",
    )
    min_reinvest_percent: Decimal = Field(
        default=Decimal("0.30"),
        description="Minimum share of post-tax profit reinvested into the machine.",
    )


class ProfitRealizationInput(BaseModel):
    """
    Inputs for realizing and allocating profit on a single deal.
    """

    backend_deal_id: int = Field(
        ...,
        description="Backend Deal.id this profit run is tied to.",
    )

    sale_price: Decimal = Field(
        ...,
        description="Actual or expected sale price of the property.",
    )
    sale_closing_costs: Decimal = Field(
        default=Decimal("0"),
        description="Closing costs on the exit (realtor, legal, etc.).",
    )
    extra_expenses: Decimal = Field(
        default=Decimal("0"),
        description="Any additional expenses not captured elsewhere.",
    )

    tax_rate: Decimal = Field(
        default=Decimal("0.25"),
        description="Effective tax rate for this profit event (0.25 = 25%).",
    )
    funfunds_percent: Decimal = Field(
        default=Decimal("0.15"),
        description="Share of post-tax profit to route to FunFunds (0.15 = 15%).",
    )
    reinvest_percent: Decimal = Field(
        default=Decimal("0.50"),
        description="Share of post-tax profit to reinvest into the machine.",
    )


class ProfitAllocationMetrics(BaseModel):
    """
    Core numbers for the profit event.
    """

    purchase_price: Decimal = Field(
        ...,
        description="Purchase price (from Deal.offer or Deal.price).",
    )
    repairs: Decimal = Field(
        ...,
        description="Total rehab/repair costs (from Deal.repairs).",
    )
    entry_closing_costs: Decimal = Field(
        ...,
        description="Estimated entry-side closing costs (if tracked).",
    )
    total_cost_basis: Decimal = Field(
        ...,
        description="Purchase + repairs + entry closing costs.",
    )
    sale_price: Decimal = Field(
        ...,
        description="Sale price as provided.",
    )
    sale_closing_costs: Decimal = Field(
        ...,
        description="Exit-side closing costs.",
    )
    extra_expenses: Decimal = Field(
        ...,
        description="Other expenses associated with this profit event.",
    )
    gross_profit: Decimal = Field(
        ...,
        description="Sale price - (cost basis + sale closing + extras).",
    )
    taxes: Decimal = Field(
        ...,
        description="Tax amount based on tax_rate applied to gross_profit (or 0 if loss).",
    )
    net_profit_after_tax: Decimal = Field(
        ...,
        description="Gross profit minus taxes.",
    )


class ProfitAllocationBreakdown(BaseModel):
    """
    Where the net profit after tax is going.
    """

    funfunds_amount: Decimal = Field(
        ...,
        description="Amount going to FunFunds (lifestyle / family / play).",
    )
    reinvest_amount: Decimal = Field(
        ...,
        description="Amount being reinvested into the machine/business.",
    )
    owner_draw_amount: Decimal = Field(
        ...,
        description="Amount available as direct owner draw / reserve.",
    )
    leftover_amount: Decimal = Field(
        ...,
        description="Any rounding or unallocated remainder.",
    )


class ProfitAllocationFlags(BaseModel):
    """
    Policy breaches / notes.
    """

    breach_min_tax_rate: bool = False
    breach_funfunds_cap: bool = False
    breach_min_reinvest: bool = False
    notes: str = ""


class ProfitAllocationResult(BaseModel):
    """
    Final result for the profit event.
    """

    metrics: ProfitAllocationMetrics
    breakdown: ProfitAllocationBreakdown
    policy: ProfitAllocationPolicy
    flags: ProfitAllocationFlags
    summary: str
    debug: Dict[str, str] = Field(default_factory=dict)


class RunProfitAllocationRequest(BaseModel):
    profit: ProfitRealizationInput
    policy: Optional[ProfitAllocationPolicy] = Field(
        default=None,
        description="Optional override of default policy.",
    )


class RunProfitAllocationResponse(BaseModel):
    backend_deal_id: int
    result: ProfitAllocationResult
    freeze_event_created: bool = Field(
        default=False,
        description="True if a freeze_event was logged due to policy breach.",
    )
