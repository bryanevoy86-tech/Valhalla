from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LokiAnalysisRequest(BaseModel):
    artifact_text: str = Field(..., description="Raw textual artifact to analyze")
    risk_profile: Optional[dict[str, Any]] = Field(
        default=None, description="Optional external risk profile hints"
    )
    context: Optional[dict[str, Any]] = Field(
        default=None, description="Additional context (e.g., originating review id)"
    )


class LokiCounterRiskCategory(BaseModel):
    hits: List[str]
    severity: str


class LokiAnalysisResponse(BaseModel):
    reverse_frame: str
    assumptions: List[str]
    risk_map: Dict[str, Any]
    worst_case: str
    suggested_corrections: List[str]
    confidence: float
    version: str
    analyzed_at: datetime

    model_config = {"from_attributes": True}
