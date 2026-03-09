"""Zone Expansion Engine Schemas"""
from typing import List, Optional

from pydantic import BaseModel


class ExpansionCriteriaStatus(BaseModel):
    brrrr_stability_met: bool
    cashflow_multiple_met: bool
    refi_cycles_met: bool
    automation_coverage_met: bool


class ZoneExpansionRecommendation(BaseModel):
    starting_zone: Optional[str] = None
    target_zone: str
    confidence: float
    criteria: ExpansionCriteriaStatus
    notes: List[str]
    action_plan: List[str]


class ZoneExpansionRequest(BaseModel):
    starting_zone: Optional[str] = None  # None = let Heimdall choose
