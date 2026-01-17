from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Mode = Literal["explore", "execute"]
DecisionBand = Literal["A", "B", "C", "D"]


class ModeSetRequest(BaseModel):
    mode: Mode = "explore"
    reason: str = ""


class PantheonState(BaseModel):
    mode: Mode = "explore"
    reason: str = ""
    last_set_at: datetime
    last_set_by: str = "api"


class DispatchRequest(BaseModel):
    intent: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    desired_band: DecisionBand = "B"


class DispatchResponse(BaseModel):
    ok: bool
    mode: Mode
    allowed: bool
    band: DecisionBand
    route: str
    suggestion: str
    warnings: List[str] = Field(default_factory=list)
