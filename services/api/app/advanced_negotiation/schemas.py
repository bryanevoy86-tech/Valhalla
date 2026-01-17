"""
Pydantic schemas for Advanced Negotiation Techniques (Pack 32).
"""
from pydantic import BaseModel, Field
from datetime import datetime


class NegotiationTechniqueCreate(BaseModel):
    technique_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    effectiveness_score: float = Field(..., ge=0.0, le=100.0, description="Effectiveness score (0-100)")
    technique_type: str | None = Field(None, max_length=100)


class NegotiationTechniqueOut(BaseModel):
    id: int
    technique_name: str
    description: str
    effectiveness_score: float
    technique_type: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TechniqueRankingRequest(BaseModel):
    min_score: float = Field(default=0.0, ge=0.0, le=100.0)
    technique_type: str | None = None
