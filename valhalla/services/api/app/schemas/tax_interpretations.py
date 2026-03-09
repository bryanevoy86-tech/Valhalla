from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class TaxOpinionCreate(BaseModel):
    jurisdiction: str
    tax_year: Optional[str] = None

    source: str  # "accountant" | "ai" | "lawyer"
    specialist_id: Optional[UUID] = None
    case_id: Optional[UUID] = None

    summary: Optional[str] = None
    details: Optional[dict[str, Any]] = None

    risk_level: Optional[str] = None
    flags: Optional[dict[str, Any]] = None


class TaxOpinionRead(BaseModel):
    id: UUID
    created_at: datetime

    jurisdiction: str
    tax_year: Optional[str] = None

    source: str
    specialist_id: Optional[UUID] = None
    case_id: Optional[UUID] = None

    summary: Optional[str] = None
    details: Optional[dict[str, Any]] = None

    risk_level: Optional[str] = None
    flags: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}
