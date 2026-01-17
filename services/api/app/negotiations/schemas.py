"""
Pydantic schemas for negotiations.
"""
from pydantic import BaseModel, Field
from datetime import datetime

class NegotiationCreate(BaseModel):
    user_id: int
    deal_id: int | None = None
    tone_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    negotiation_stage: str = "initial"

class NegotiationOut(BaseModel):
    id: int
    user_id: int
    deal_id: int | None
    tone_score: float
    sentiment_score: float
    negotiation_stage: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
