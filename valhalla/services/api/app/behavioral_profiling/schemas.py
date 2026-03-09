"""
Pydantic schemas for Behavioral Profiling.
"""
from pydantic import BaseModel, Field
from datetime import datetime


class BehavioralProfileCreate(BaseModel):
    user_id: int
    lead_id: int | None = None
    behavioral_score: float = Field(..., ge=0.0, le=100.0, description="Engagement score 0-100")
    interests: str | None = Field(None, max_length=500, description="Comma-separated interests")
    engagement_level: str = Field(default="low", max_length=50)
    last_engaged_at: datetime | None = None


class BehavioralProfileOut(BaseModel):
    id: int
    user_id: int
    lead_id: int | None
    behavioral_score: float
    interests: str | None
    engagement_level: str
    last_engaged_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BehavioralProfileUpdate(BaseModel):
    behavioral_score: float | None = Field(None, ge=0.0, le=100.0)
    interests: str | None = Field(None, max_length=500)
    engagement_level: str | None = Field(None, max_length=50)
    last_engaged_at: datetime | None = None


class EngagementRecommendation(BaseModel):
    """AI-driven recommendation for user engagement."""
    user_id: int
    recommended_strategy: str
    confidence_score: float
    reasoning: str
