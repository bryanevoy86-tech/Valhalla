"""PACK-PRELAUNCH-12: BRRRR Stability Engine Schemas"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BRRRRStabilityBase(BaseModel):
    property_address: str
    stability_score: float
    risk_factors: Optional[dict[str, Any]] = None
    recommendations: Optional[dict[str, Any]] = None


class BRRRRStabilityRead(BRRRRStabilityBase):
    id: UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
