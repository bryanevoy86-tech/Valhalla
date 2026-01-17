# services/api/app/schemas/pro_scorecard.py

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field


class ProfessionalIn(BaseModel):
    name: str
    role: str
    organization: Optional[str] = None
    public_urls: Optional[str] = Field(
        None, description="Comma-separated URLs for behavioral extraction."
    )


class ProfessionalOut(ProfessionalIn):
    id: int

    class Config:
        from_attributes = True


class InteractionLogIn(BaseModel):
    response_time_hours: Optional[float] = None
    deliverable_quality: Optional[float] = Field(None, description="0–1 rating")
    communication_clarity: Optional[float] = Field(None, description="0–1 rating")
    met_deadline: Optional[bool] = None
    notes: Optional[str] = None


class InteractionLogOut(InteractionLogIn):
    id: int
    date: str

    class Config:
        from_attributes = True


class ScorecardOut(BaseModel):
    reliability_score: float
    communication_score: float
    quality_score: float
    overall_score: float

    class Config:
        from_attributes = True
