from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class AutopayPlanRequest(BaseModel):
    obligation_id: str
    bank: str = ""              # "RBC", "TD", etc (optional)
    mode: Literal["guidance", "checklist"] = "checklist"
    meta: Dict[str, Any] = Field(default_factory=dict)


class AutopayPlanResponse(BaseModel):
    obligation_id: str
    obligation_name: str = ""
    autopay_recommended: bool = True
    checklist: List[str] = Field(default_factory=list)
    reminders: List[str] = Field(default_factory=list)
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
