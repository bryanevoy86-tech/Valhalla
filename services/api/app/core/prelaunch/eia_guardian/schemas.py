"""PACK-PRELAUNCH-10: EIA Guardian Engine Schemas"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EIAStatusRead(BaseModel):
    id: UUID
    monthly_limit: float
    current_income: float
    projected_income: float
    risk_level: str
    recommendations: Optional[dict[str, Any]] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
