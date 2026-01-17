from __future__ import annotations

from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field


Risk = Literal["safe", "medium", "aggressive"]


class RiskAssessRequest(BaseModel):
    category: str = ""
    tags: List[str] = Field(default_factory=list)
    vendor: str = ""
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)


class RiskAssessResponse(BaseModel):
    risk: Risk
    score: float
    reasons: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
