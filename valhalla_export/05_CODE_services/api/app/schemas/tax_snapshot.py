# services/api/app/schemas/tax_snapshot.py

from __future__ import annotations

from decimal import Decimal
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class TaxSnapshotInput(BaseModel):
    """
    Inputs needed to build a CRA-style tax snapshot for a single deal.

    We deliberately mirror the profit_allocation inputs so this is a thin
    wrapper around that flow.
    """

    backend_deal_id: int = Field(
        ...,
        description="Backend Deal.id this tax snapshot is tied to.",
    )

    sale_price: Decimal = Field(
        ...,
        ge=0,
        description="Actual or expected sale price of the property.",
    )
    sale_closing_costs: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Closing costs on the exit (realtor, legal, etc.).",
    )
    extra_expenses: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Any additional expenses not captured elsewhere.",
    )

    tax_rate: Decimal = Field(
        default=Decimal("0.25"),
        ge=0,
        le=1,
        description="Effective tax rate applied to profit (0.25 = 25%).",
    )


class TaxSnapshotPolicy(BaseModel):
    """
    Policy view of taxes for this snapshot.
    """

    min_tax_rate: Decimal = Field(
        default=Decimal("0.20"),
        description="Minimum effective tax rate allowed by your internal rules.",
    )
    breach_min_tax_rate: bool = Field(
        default=False,
        description="True if tax_rate < min_tax_rate and there is positive profit.",
    )
    notes: Optional[str] = None


class TaxSnapshotNumbers(BaseModel):
    """
    CRA-style numeric breakdown for a single deal.
    """

    purchase_price: Decimal
    repairs: Decimal
    cost_basis: Decimal
    sale_price: Decimal
    sale_closing_costs: Decimal
    extra_expenses: Decimal
    gross_profit: Decimal
    taxable_profit: Decimal
    tax_rate_applied: Decimal
    tax_amount: Decimal
    net_after_tax: Decimal

    @field_serializer('purchase_price', 'repairs', 'cost_basis', 'sale_price',
                      'sale_closing_costs', 'extra_expenses', 'gross_profit',
                      'taxable_profit', 'tax_rate_applied', 'tax_amount', 'net_after_tax')
    def serialize_decimal_as_float(self, value: Decimal) -> float:
        return float(value)


class TaxSnapshotResponse(BaseModel):
    """
    Final tax snapshot for a single deal.
    """

    backend_deal_id: int
    numbers: TaxSnapshotNumbers
    policy: TaxSnapshotPolicy
    summary: str
    debug: Dict[str, str] = Field(default_factory=dict)
