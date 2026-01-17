"""
Gate functions for safety and autonomy checks.

Apply hard constraints before allowing decision execution.
"""

from __future__ import annotations
from .schemas import DecisionCandidate, UnifiedPolicy


def safety_gate(c: DecisionCandidate, policy: UnifiedPolicy) -> tuple[bool, str]:
    """
    Apply safety gate checks.
    
    Checks:
    - Risk per action does not exceed cap
    - Exposure per leg does not exceed cap
    
    Args:
        c: The decision candidate
        policy: The Unified Policy
    
    Returns:
        tuple: (passes: bool, reason: str)
    """
    s = policy.safety

    if c.proposed_risk_pct_of_capital > s.max_risk_per_action_pct:
        return (
            False,
            f"Risk per action exceeds cap "
            f"({c.proposed_risk_pct_of_capital}% > {s.max_risk_per_action_pct}%)"
        )

    if c.proposed_exposure_pct_of_leg > s.max_exposure_per_leg_pct:
        return (
            False,
            f"Exposure per leg exceeds cap "
            f"({c.proposed_exposure_pct_of_leg}% > {s.max_exposure_per_leg_pct}%)"
        )

    return True, "OK"


def autonomy_gate(
    c: DecisionCandidate,
    policy: UnifiedPolicy,
    samples_for_leg: int
) -> tuple[bool, str]:
    """
    Apply autonomy gate checks.
    
    Checks:
    - Sufficient samples for requested autonomy level
    - Variance within limits for the autonomy level
    
    Args:
        c: The decision candidate
        policy: The Unified Policy
        samples_for_leg: Number of historical samples for this leg
    
    Returns:
        tuple: (passes: bool, reason: str)
    """
    a = policy.autonomy

    # Determine if requested autonomy level is allowed by samples
    required = {
        "L0": 0,
        "L1": a.l1_recommend_min_samples,
        "L2": a.l2_auto_execute_min_samples,
        "L3": a.l3_auto_scale_min_samples,
        "L4": a.l4_auto_prune_min_samples,
    }[c.autonomy_level]

    if samples_for_leg < required:
        return (
            False,
            f"Autonomy {c.autonomy_level} requires {required} samples; "
            f"have {samples_for_leg}"
        )

    # Variance caps (if provided)
    if c.estimated_variance_pct is not None:
        if c.autonomy_level == "L2" and c.estimated_variance_pct > a.l2_max_variance_pct:
            return (
                False,
                f"Variance too high for L2 "
                f"({c.estimated_variance_pct}% > {a.l2_max_variance_pct}%)"
            )
        if c.autonomy_level == "L3" and c.estimated_variance_pct > a.l3_max_variance_pct:
            return (
                False,
                f"Variance too high for L3 "
                f"({c.estimated_variance_pct}% > {a.l3_max_variance_pct}%)"
            )
        if c.autonomy_level == "L4" and c.estimated_variance_pct > a.l4_max_variance_pct:
            return (
                False,
                f"Variance too high for L4 "
                f"({c.estimated_variance_pct}% > {a.l4_max_variance_pct}%)"
            )

    return True, "OK"
