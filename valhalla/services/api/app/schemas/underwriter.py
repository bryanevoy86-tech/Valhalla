from pydantic import BaseModel
from typing import Optional

class UnderwriterAssessmentBase(BaseModel):
    deal_id: int
    risk_score: float = 0.0
    legal_risk_score: float = 0.0
    profitability_score: float = 0.0
    decision: str = "review"
    notes: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    legal_profile_id: Optional[int] = None

class UnderwriterAssessmentCreate(UnderwriterAssessmentBase):
    pass

class UnderwriterAssessmentUpdate(BaseModel):
    risk_score: Optional[float]
    legal_risk_score: Optional[float]
    profitability_score: Optional[float]
    decision: Optional[str]
    notes: Optional[str]
    country: Optional[str]
    region: Optional[str]
    legal_profile_id: Optional[int]

class UnderwriterAssessmentOut(UnderwriterAssessmentBase):
    id: int

    class Config:
        orm_mode = True
