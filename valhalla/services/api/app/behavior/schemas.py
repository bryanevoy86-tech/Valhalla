"""
Pack 48: Heimdall Behavioral Core
Pydantic schemas for behavior scoring, script selection, and session tracking
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class BehaviorFeatures(BaseModel):
    """Input features for behavioral scoring"""
    trust: float = 0.0
    urgency: float = 0.0
    resistance: float = 0.0
    sentiment: float = 0.0
    authority: float = 0.0
    tone: str = "neutral"


class ScoreOut(BaseModel):
    """Weighted score output"""
    score: float
    persona: str
    confidence: float


class ScriptRequest(BaseModel):
    """Request for script snippet selection"""
    persona: str
    intent: str
    tone: str
    confidence: float = 0.5


class ScriptOut(BaseModel):
    """Script snippet response"""
    snippet_name: str
    persona: str
    intent: str
    tone: str
    text: str
    model_config = ConfigDict(from_attributes=True)


class SessionStart(BaseModel):
    """Start a negotiation session"""
    session_id: str
    persona: str
    lead_id: Optional[int] = None
    deal_id: Optional[int] = None


class SessionOut(BaseModel):
    """Negotiation session output"""
    id: int
    session_id: str
    persona: str
    lead_id: Optional[int] = None
    deal_id: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    outcome: Optional[str] = None
    summary: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class EventIn(BaseModel):
    """Log a behavior event"""
    session_id: str
    event_type: str
    speaker: str
    text: Optional[str] = None
    trust_score: Optional[float] = None
    urgency_score: Optional[float] = None
    resistance_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    authority_score: Optional[float] = None
    tone: Optional[str] = None
    intent: Optional[str] = None


class EventOut(BaseModel):
    """Behavior event output"""
    id: int
    session_id: str
    event_type: str
    speaker: str
    text: Optional[str] = None
    trust_score: Optional[float] = None
    urgency_score: Optional[float] = None
    resistance_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    authority_score: Optional[float] = None
    tone: Optional[str] = None
    intent: Optional[str] = None
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


class WeightIn(BaseModel):
    """Update behavior weights for a persona"""
    trust_weight: float = 1.0
    urgency_weight: float = 1.0
    resistance_weight: float = 1.0
    sentiment_weight: float = 1.0
    authority_weight: float = 1.0
    tone_weight: float = 1.0


class WeightOut(BaseModel):
    """Behavior weight output"""
    id: int
    persona: str
    trust_weight: float
    urgency_weight: float
    resistance_weight: float
    sentiment_weight: float
    authority_weight: float
    tone_weight: float
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
