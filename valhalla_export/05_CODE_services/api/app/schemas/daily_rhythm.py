"""
PACK TO: Daily Rhythm & Tempo Schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class TimeBlock(BaseModel):
    start: str
    end: str


class DailyRhythmProfileCreate(BaseModel):
    name: str = "default"
    wake_time: Optional[str] = None
    sleep_time: Optional[str] = None
    peak_focus_blocks: Optional[List[TimeBlock]] = None
    low_energy_blocks: Optional[List[TimeBlock]] = None
    family_blocks: Optional[List[TimeBlock]] = None
    personal_time_blocks: Optional[List[TimeBlock]] = None
    notes: Optional[str] = None
    active: bool = True


class DailyRhythmProfileOut(DailyRhythmProfileCreate):
    id: int

    class Config:
        from_attributes = True


class TempoRuleCreate(BaseModel):
    profile_name: str = "default"
    time_block: str
    action_intensity: str
    communication_style: str
    notes: Optional[str] = None


class TempoRuleOut(TempoRuleCreate):
    id: int

    class Config:
        from_attributes = True


class DailyRhythmSnapshot(BaseModel):
    profile: DailyRhythmProfileOut
    rules: List[TempoRuleOut]
    meta: Dict[str, Any] = {}
