# app/ai/models.py
from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class DecisionProposal(BaseModel):
    """
    Generic decision payload that Heimdall/Loki will evaluate.
    Example payload fields (flexible):
      - risk_score: float 0.0–1.0
      - amount: numeric value for money decisions
      - context: free-form dict with extra info
    """
    id: str
    domain: str
    payload: Dict[str, Any] = {}


class AgentVerdict(BaseModel):
    agent_name: str
    approved: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: List[str] = []
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}


class ArbitrationOutcome(BaseModel):
    decision_id: str
    domain: str

    final_approved: bool
    consensus: float  # 0.0–1.0, how aligned the agents are
    primary_agent: str
    secondary_agent: str | None = None

    notes: List[str] = []
    flags: List[str] = []
    raw: Dict[str, Any] = {}
