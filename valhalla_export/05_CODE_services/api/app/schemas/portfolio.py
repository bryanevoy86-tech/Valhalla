# services/api/app/schemas/portfolio.py

from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DealStatusCounts(BaseModel):
    draft: int = 0
    active: int = 0
    under_contract: int = 0
    sold: int = 0
    archived: int = 0


class PortfolioDealSnapshot(BaseModel):
    id: int
    status: str
    region: Optional[str] = None
    property_type: Optional[str] = None
    price: Optional[Decimal] = None
    arv: Optional[Decimal] = None
    repairs: Optional[Decimal] = None
    offer: Optional[Decimal] = None
    mao: Optional[Decimal] = None
    headline: Optional[str] = None
    has_freeze: bool = False
    freeze_severity: Optional[str] = None


class FreezeSummaryCounts(BaseModel):
    total_events: int = 0
    info: int = 0
    warn: int = 0
    critical: int = 0
    unresolved: int = 0


class PortfolioSummary(BaseModel):
    total_deals: int
    status_counts: DealStatusCounts
    estimated_gross_profit_active: Optional[Decimal] = Field(
        default=None,
        description="Sum of (ARV - (price+repairs)) for active/under_contract where data exists.",
    )
    estimated_gross_profit_sold: Optional[Decimal] = Field(
        default=None,
        description="Sum of (sale_price - cost_basis) from closed deals if data is available.",
    )
    freeze_counts: FreezeSummaryCounts
    notes: Optional[str] = None
    debug: Dict[str, str] = Field(default_factory=dict)


class PortfolioDealsResponse(BaseModel):
    summary: PortfolioSummary
    deals: List[PortfolioDealSnapshot]
