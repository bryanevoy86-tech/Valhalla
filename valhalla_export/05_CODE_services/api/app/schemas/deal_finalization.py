# services/api/app/schemas/deal_finalization.py

from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel, Field


class DealFinalizationStatus(BaseModel):
    deal_id: int
    ready: bool = Field(..., description="True if all requirements met for finalization")
    checklist: Dict[str, bool] = Field(..., description="Breakdown of finalization requirements")
    finalized: Optional[bool] = Field(None, description="True if deal has been finalized")
