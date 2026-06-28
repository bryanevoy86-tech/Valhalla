from typing import Any, Dict, List


def detect_buyer_missing_data(deal: Dict[str, Any]) -> List[str]:
    required = [
        "property_address",
        "city",
        "strategy",
        "arv",
        "contract_price",
        "estimated_repairs",
        "target_buyer_price",
        "verified_cash_buyers_count",
        "recent_investor_sales_count",
        "buyer_feedback_score",
        "days_to_close_expectation",
    ]

    return [
        key for key in required
        if key not in deal or deal.get(key) in [None, ""]
    ]


def score_cash_buyer_depth(count: int) -> int:
    if count >= 20:
        return 25
    if count >= 10:
        return 20
    if count >= 5:
        return 14
    if count >= 2:
        return 7
    return 0


def score_recent_investor_activity(count: int) -> int:
    if count >= 20:
        return 20
    if count >= 10:
        return 16
    if count >= 5:
        return 10
    if count >= 2:
        return 5
    return 0


def score_buyer_feedback(feedback_score: int) -> int:
    """
    Buyer feedback score is expected from 0-10.
    Convert to max 20 points.
    """
    return max(0, min(feedback_score, 10)) * 2


def score_spread_strength(contract_price: float, target_buyer_price: float) -> int:
    spread = target_buyer_price - contract_price

    if spread >= 50000:
        return 20
    if spread >= 30000:
        return 16
    if spread >= 20000:
        return 12
    if spread >= 10000:
        return 7
    return 0


def score_close_speed(days: int) -> int:
    if days <= 7:
        return 15
    if days <= 14:
        return 12
    if days <= 21:
        return 8
    if days <= 30:
        return 4
    return 0


def detect_disposition_red_flags(deal: Dict[str, Any]) -> List[str]:
    flags = []

    if int(deal.get("verified_cash_buyers_count", 0) or 0) < 2:
        flags.append("buyer_pool_too_thin")

    if int(deal.get("recent_investor_sales_count", 0) or 0) < 2:
        flags.append("weak_recent_investor_activity")

    if float(deal.get("target_buyer_price", 0) or 0) <= float(deal.get("contract_price", 0) or 0):
        flags.append("no_assignment_spread")

    if deal.get("buyer_feedback_score", 0) < 4:
        flags.append("negative_buyer_feedback")

    if deal.get("major_rehab_required", False) and not deal.get("rehab_buyer_confirmed", False):
        flags.append("major_rehab_without_rehab_buyer")

    if deal.get("rural_or_low_liquidity_area", False):
        flags.append("low_liquidity_area")

    return flags


def evaluate_buyer_demand(deal: Dict[str, Any]) -> Dict[str, Any]:
    missing_data = detect_buyer_missing_data(deal)
    red_flags = detect_disposition_red_flags(deal)

    score = 0

    score += score_cash_buyer_depth(int(deal.get("verified_cash_buyers_count", 0) or 0))
    score += score_recent_investor_activity(int(deal.get("recent_investor_sales_count", 0) or 0))
    score += score_buyer_feedback(int(deal.get("buyer_feedback_score", 0) or 0))
    score += score_spread_strength(
        float(deal.get("contract_price", 0) or 0),
        float(deal.get("target_buyer_price", 0) or 0),
    )
    score += score_close_speed(int(deal.get("days_to_close_expectation", 999) or 999))

    score = max(0, min(score, 100))

    hard_stops = [
        "buyer_pool_too_thin",
        "no_assignment_spread",
        "major_rehab_without_rehab_buyer",
    ]

    has_hard_stop = any(flag in red_flags for flag in hard_stops)

    if has_hard_stop:
        recommendation = "DO_NOT_CONTRACT_YET"
        next_action = "Build buyer demand or renegotiate before contracting."
    elif missing_data:
        recommendation = "HOLD_MISSING_DISPOSITION_DATA"
        next_action = "Collect buyer/disposition data before proceeding."
    elif score >= 80:
        recommendation = "STRONG_DISPOSITION_CONFIDENCE"
        next_action = "Proceed only if underwriting and legal gates are also green."
    elif score >= 60:
        recommendation = "MODERATE_DISPOSITION_CONFIDENCE"
        next_action = "Proceed cautiously. Get soft buyer commitments first."
    elif score >= 40:
        recommendation = "WEAK_DISPOSITION_CONFIDENCE"
        next_action = "Do not contract unless price is renegotiated lower."
    else:
        recommendation = "DO_NOT_CONTRACT_YET"
        next_action = "Buyer demand too weak. Pass, renegotiate, or build buyer list."

    return {
        "buyer_demand_score": score,
        "recommendation": recommendation,
        "missing_data": missing_data,
        "red_flags": red_flags,
        "next_action": next_action,
        "human_approval_required": True,
    }
