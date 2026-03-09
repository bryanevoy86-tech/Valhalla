from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class BuyerIn(BaseModel):
    name: str
    contact: str | None = None  # phone/email
    country: str = "CA"         # CA|US
    province_state: str | None = None
    city: str | None = None

    # preferences
    strategies: List[str] = ["wholesale"]
    property_types: List[str] = ["sfh"]
    min_arv: float | None = None
    max_arv: float | None = None
    max_repairs: float | None = None
    min_equity_pct: float | None = Field(default=15.0, description="minimum equity %")
    close_speed_days: int | None = None

    tags: List[str] = []
    notes: str | None = None
    meta: Dict[str, Any] = {}

class Buyer(BuyerIn):
    id: str
    created_at_utc: str
    updated_at_utc: str | None = None
