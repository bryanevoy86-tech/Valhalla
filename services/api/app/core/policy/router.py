"""
Policy API router.

Endpoints:
- GET /policy - Retrieve the current policy
- POST /policy/evaluate - Evaluate a decision candidate
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from .loader import load_policy
from .schemas import DecisionCandidate
from .scoring import compute_score, passes_minimums
from .gates import safety_gate, autonomy_gate

router = APIRouter(prefix="/policy", tags=["policy"])


@router.get("", summary="Get the current policy")
def get_policy():
    """
    Retrieve the complete Unified Policy configuration.
    
    Returns:
        dict: The policy object with all thresholds, limits, and settings.
    """
    return load_policy().model_dump()


@router.post("/evaluate", summary="Evaluate a decision candidate")
def evaluate_candidate(
    candidate: DecisionCandidate,
    samples_for_leg: int = 0
):
    """
    Evaluate a decision candidate against the Unified Policy.
    
    Applies gates in order:
    1. Safety gate (risk/exposure caps)
    2. Autonomy gate (sample requirements + variance)
    3. Optimization minimums (EV, confidence, downside/EV ratio)
    4. Scoring (if all gates pass)
    
    Args:
        candidate: The decision candidate to evaluate
        samples_for_leg: Number of historical samples for autonomy assessment
    
    Returns:
        dict: Evaluation result with:
        - allowed (bool): Whether the decision is allowed
        - stage (str): Which gate failed (if not allowed)
        - reason (str): Explanation
        - score (float): Computed score (if allowed)
    """
    policy = load_policy()

    # Stage 1: Safety gate
    ok, reason = safety_gate(candidate, policy)
    if not ok:
        return {
            "allowed": False,
            "stage": "safety",
            "reason": reason
        }

    # Stage 2: Autonomy gate
    ok, reason = autonomy_gate(candidate, policy, samples_for_leg=samples_for_leg)
    if not ok:
        return {
            "allowed": False,
            "stage": "autonomy",
            "reason": reason
        }

    # Stage 3: Optimization minimums
    ok, reason = passes_minimums(candidate, policy)
    if not ok:
        return {
            "allowed": False,
            "stage": "optimization_minimums",
            "reason": reason
        }

    # Stage 4: Scoring
    score = compute_score(candidate, policy)
    return {
        "allowed": True,
        "score": round(score, 4),
        "reason": "OK"
    }
