from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GrantIn(BaseModel):
    name: str
    provider: str | None = None  # Gov dept / org
    country: str = "CA"          # CA|US
    province_state: str | None = None
    city: str | None = None

    category: str = "general"    # hiring|green|innovation|export|training|youth|women|indigenous|general
    stage: str = "startup"       # idea|startup|operating|scaling
    amount_min: float | None = None
    amount_max: float | None = None

    deadline_utc: str | None = None  # ISO string
    eligibility_notes: str | None = None
    url: str | None = None

    required_docs: List[str] = []
    tags: List[str] = []
    notes: str | None = None
    meta: Dict[str, Any] = {}


class Grant(GrantIn):
    id: str
    created_at_utc: str
    updated_at_utc: str
