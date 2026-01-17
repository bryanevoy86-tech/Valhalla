from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Severity = Literal["low", "medium", "high", "critical"]


class CheckFinding(BaseModel):
    code: str
    severity: Severity
    message: str
    action_hint: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)


class WeeklyCheckResponse(BaseModel):
    ok: bool
    generated_at: datetime
    findings: List[CheckFinding] = Field(default_factory=list)
    created_followups: int = 0
    created_alerts: int = 0
