from __future__ import annotations

from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class GoStep(BaseModel):
    id: str
    title: str
    why: str
    band_min: str = Field(default="B", description="Minimum Cone band this step is designed for (A/B/C/D).")
    blocked_if_red: bool = Field(default=True, description="If status is RED, step is blocked.")
    done: bool = False
    notes: Optional[str] = None

class GoChecklist(BaseModel):
    cone_band: str
    status: str
    steps: List[GoStep]
    blocked_reasons: List[str] = []

class CompleteStepRequest(BaseModel):
    step_id: str
    done: bool = True
    notes: Optional[str] = None

class GoNext(BaseModel):
    cone_band: str
    status: str
    next_step: Optional[GoStep] = None
    message: str
