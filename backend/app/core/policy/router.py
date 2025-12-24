from __future__ import annotations

from fastapi import APIRouter
from .loader import load_policy, reload_policy
from .schemas import DecisionCandidate
from .scoring import compute_score, passes_minimums
from .gates import safety_gate, autonomy_gate

router = APIRouter(prefix="/policy", tags=["policy"])


@router.get("")
def get_policy():
    return load_policy().model_dump()


@router.post("/reload")
def reload():
    return reload_policy().model_dump()


@router.post("/evaluate")
def evaluate_candidate(candidate: DecisionCandidate, samples_for_leg: int = 0):
    policy = load_policy()

    ok, reason = safety_gate(candidate, policy)
    if not ok:
        return {"allowed": False, "stage": "safety", "reason": reason}

    ok, reason = autonomy_gate(candidate, policy, samples_for_leg=samples_for_leg)
    if not ok:
        return {"allowed": False, "stage": "autonomy", "reason": reason}

    ok, reason = passes_minimums(candidate, policy)
    if not ok:
        return {"allowed": False, "stage": "optimization_minimums", "reason": reason}

    score = compute_score(candidate, policy)
    return {"allowed": True, "score": score, "reason": "OK"}
