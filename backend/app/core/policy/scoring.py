from __future__ import annotations

from .schemas import DecisionCandidate, UnifiedPolicy


def compute_score(c: DecisionCandidate, policy: UnifiedPolicy) -> float:
    w_risk = policy.optimization.score_weights.get("risk_weight", 0.8)
    w_time = policy.optimization.score_weights.get("time_penalty_weight", 0.2)

    soft_cap = max(1, policy.optimization.time_to_cash_months_soft_cap)
    time_penalty = min(1.0, c.time_to_cash_months / soft_cap)

    risk = c.downside
    score = c.ev - (w_risk * risk) - (w_time * time_penalty) + c.strategic_value
    return score


def passes_minimums(c: DecisionCandidate, policy: UnifiedPolicy) -> tuple[bool, str]:
    if c.ev <= policy.optimization.min_ev:
        return False, f"EV below minimum ({c.ev} <= {policy.optimization.min_ev})"
    if c.confidence_pct < policy.optimization.min_confidence_pct:
        return False, f"Confidence below minimum ({c.confidence_pct} < {policy.optimization.min_confidence_pct})"
    if c.ev <= 0:
        return False, "EV must be > 0"

    ratio = c.downside / c.ev
    if ratio > policy.optimization.max_downside_to_ev_ratio:
        return False, f"Downside/EV too high ({ratio:.3f} > {policy.optimization.max_downside_to_ev_ratio})"

    return True, "OK"
