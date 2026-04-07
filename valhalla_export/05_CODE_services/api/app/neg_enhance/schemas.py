"""
Pack 52: Negotiation & Psychology AI Enhancer - Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict


class AnalyzeReq(BaseModel):
    text: str = Field(min_length=1)
    persona: Optional[str] = None


class AnalyzeOut(BaseModel):
    sentiment: float    # -1..1
    tone: Literal["calm","assertive","empathetic","analytical"]
    intent: Literal["info","objection","decision","stall"]
    confidence: float   # 0..1
    objection_code: Optional[str] = None


class RebuttalReq(BaseModel):
    persona: Optional[str] = None
    tone: Optional[str] = None
    objection_code: str


class RebuttalOut(BaseModel):
    content: str
    confidence: float


class RewardIn(BaseModel):
    session_id: int
    signal: Literal["win","progress","stall","lost"]
    weight: float = 1.0
    notes: Optional[str] = None


class EscalateCheckIn(BaseModel):
    session_id: int
    conf_score: float
    persona: Optional[str] = None


class EscalateOut(BaseModel):
    should_escalate: bool
    action: Optional[str] = None
    payload: Optional[Dict] = None
