from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ArbitrationRequest(BaseModel):
    heimdall_summary: str = Field(..., description="Summary stance from Heimdall")
    loki_summary: str = Field(..., description="Summary stance from Loki")
    heimdall_risk_tier: str = Field(..., description="Risk tier assigned by Heimdall")
    loki_risk_tier: str = Field(..., description="Risk tier assigned by Loki")
    dispute_context: Optional[dict[str, Any]] = None
    verdict_context: Optional[dict[str, Any]] = None


class ArbitrationResponse(BaseModel):
    final_recommendation: str
    merged_risk_tier: str
    consensus: str
    confidence: float
    reasoning: Dict[str, Any]
    version: str
    decided_at: datetime

    model_config = {"from_attributes": True}
