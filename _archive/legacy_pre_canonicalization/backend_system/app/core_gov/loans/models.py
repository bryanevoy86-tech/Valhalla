from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel


class LoanIn(BaseModel):
    name: str
    lender: str | None = None
    country: str = "CA"          # CA|US
    province_state: str | None = None

    product_type: str = "microloan"   # microloan|term|loc|equipment|credit_union|vendor|sba|private
    min_amount: float | None = None
    max_amount: float | None = None

    requires_credit_history: bool = True
    requires_revenue_history: bool = False
    requires_residency: bool = False
    notes: str | None = None
    url: str | None = None

    required_docs: List[str] = []
    tags: List[str] = []
    meta: Dict[str, Any] = {}


class Loan(LoanIn):
    id: str
    created_at_utc: str
    updated_at_utc: str
