"""
Pydantic schemas for Adaptive Negotiator.
"""
from pydantic import BaseModel, Field
from datetime import datetime

class StrategyCreate(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None

class StrategyOut(BaseModel):
    id: int
    name: str
    description: str | None
    category: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class StrategySuggestionRequest(BaseModel):
    tone_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
