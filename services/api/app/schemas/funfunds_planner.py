# services/api/app/schemas/funfunds_planner.py

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer


class FixedBill(BaseModel):
    """
    A single fixed monthly bill (rent, utilities, subscriptions, etc.).
    """

    name: str
    amount: Decimal = Field(
        ...,
        ge=0,
        description="Monthly amount for this bill.",
    )
    category: str = Field(
        default="general",
        description="Optional category (housing, utilities, tools, etc.).",
    )


class FunFundsPlanInput(BaseModel):
    """
    Inputs for the monthly FunFunds plan.

    This is the Valhalla-level budgeting dial for:
    - survival (bills)
    - safety (reserve)
    - debt paydown
    - play (FunFunds)
    - reinvestment into the machine
    """

    month_label: str = Field(
        ...,
        description="Human label for the month (e.g. '2025-01', 'Jan 2025').",
    )
    gross_income: Decimal = Field(
        ...,
        ge=0,
        description="Total income for the month (all sources).",
    )
    fixed_bills: List[FixedBill] = Field(
        default_factory=list,
        description="List of fixed monthly obligations.",
    )
    min_safety_reserve_percent: Decimal = Field(
        default=Decimal("0.10"),
        ge=0,
        le=1,
        description="Minimum share of net after bills to keep as safety reserve (0.10 = 10%).",
    )
    funfunds_percent: Decimal = Field(
        default=Decimal("0.15"),
        ge=0,
        le=1,
        description="Target share of net after bills to allocate to FunFunds.",
    )
    debt_paydown_percent: Decimal = Field(
        default=Decimal("0.15"),
        ge=0,
        le=1,
        description="Target share of net after bills for debt paydown.",
    )
    reinvest_percent: Decimal = Field(
        default=Decimal("0.40"),
        ge=0,
        le=1,
        description="Target share of net after bills to reinvest into the machine.",
    )

    @field_validator(
        "funfunds_percent",
        "debt_paydown_percent",
        "reinvest_percent",
        mode="after",
    )
    def validate_total_allocation(cls, v: Decimal, values: Dict) -> Decimal:
        """
        We don't enforce exact sum=1.0, but we do allow sums >1.0 and handle
        scaling at runtime. This validator is just here for future hooks.
        """
        return v


class FunFundsAllocation(BaseModel):
    """
    Resulting allocation for the month.
    """

    bills_total: Decimal
    safety_reserve: Decimal
    funfunds_amount: Decimal
    debt_paydown_amount: Decimal
    reinvest_amount: Decimal
    leftover_amount: Decimal
    
    @field_serializer('bills_total', 'safety_reserve', 'funfunds_amount', 
                      'debt_paydown_amount', 'reinvest_amount', 'leftover_amount')
    def serialize_decimal_as_float(self, value: Decimal) -> float:
        return float(value)


class FunFundsPolicyFlags(BaseModel):
    """
    Flags if your requested dials are out of sync with baseline policy.
    """

    breach_safety_minimum: bool = False
    notes: Optional[str] = None


class FunFundsPlanResponse(BaseModel):
    """
    Full monthly plan output.
    """

    month_label: str
    gross_income: Decimal
    bills_total: Decimal
    net_after_bills: Decimal
    allocation: FunFundsAllocation
    policy_flags: FunFundsPolicyFlags
    debug: Dict[str, str] = Field(default_factory=dict)
    
    @field_serializer('gross_income', 'bills_total', 'net_after_bills')
    def serialize_decimal_as_float(self, value: Decimal) -> float:
        return float(value)
