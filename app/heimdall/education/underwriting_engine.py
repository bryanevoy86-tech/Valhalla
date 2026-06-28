from typing import Any, Dict, List, Optional


def calculate_mao(
    arv: float,
    repairs: float,
    assignment_fee: float = 15000,
    safety_buffer: float = 10000,
    arv_rule: float = 0.70,
) -> float:
    """
    Maximum Allowable Offer.
    Default wholesale formula:
    MAO = (ARV x 70%) - repairs - assignment fee - safety buffer
    """
    return round((arv * arv_rule) - repairs - assignment_fee - safety_buffer, 2)


def calculate_wholesale_spread(contract_price: float, buyer_price: float) -> float:
    return round(buyer_price - contract_price, 2)


def calculate_flip_profit(
    arv: float,
    purchase_price: float,
    repairs: float,
    closing_costs: float = 0,
    holding_costs: float = 0,
    selling_costs: float = 0,
) -> float:
    return round(arv - purchase_price - repairs - closing_costs - holding_costs - selling_costs, 2)


def calculate_flip_roi(profit: float, cash_in: float) -> Optional[float]:
    if cash_in <= 0:
        return None
    return round((profit / cash_in) * 100, 2)


def calculate_brrrr_cashflow(
    monthly_rent: float,
    mortgage_payment: float,
    taxes: float,
    insurance: float,
    repairs_reserve: float,
    vacancy_reserve: float,
    property_management: float = 0,
) -> float:
    return round(
        monthly_rent
        - mortgage_payment
        - taxes
        - insurance
        - repairs_reserve
        - vacancy_reserve
        - property_management,
        2,
    )


def detect_missing_data(deal: Dict[str, Any]) -> List[str]:
    required = [
        "strategy",
        "arv",
        "purchase_price",
        "repairs",
        "seller_authority_verified",
        "arv_supported",
        "repair_confidence",
        "buyer_demand_verified",
        "legal_review_required",
    ]

    missing = []
    for key in required:
        if key not in deal or deal.get(key) in [None, ""]:
            missing.append(key)

    return missing


def detect_red_flags(deal: Dict[str, Any]) -> List[str]:
    flags = []

    if not deal.get("seller_authority_verified", False):
        flags.append("seller_authority_unverified")

    if not deal.get("arv_supported", False):
        flags.append("arv_not_supported")

    if deal.get("repair_confidence", "low") == "low":
        flags.append("repair_budget_guess")

    if not deal.get("buyer_demand_verified", False):
        flags.append("buyer_demand_missing")

    if deal.get("legal_review_required", False) and not deal.get("lawyer_review_complete", False):
        flags.append("legal_review_required_but_not_complete")

    if deal.get("numbers_best_case_only", False):
        flags.append("numbers_only_work_best_case")

    if deal.get("title_issue_known", False):
        flags.append("title_issue_unresolved")

    return flags


def score_deal(deal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scores a deal from 0-100 using Heimdall's locked education weights.
    """

    score = 0

    seller_motivation = deal.get("seller_motivation_score", 0)
    spread_margin = deal.get("spread_margin_score", 0)
    arv_confidence = deal.get("arv_confidence_score", 0)
    repair_confidence = deal.get("repair_confidence_score", 0)
    buyer_demand = deal.get("buyer_demand_score", 0)
    legal_clarity = deal.get("legal_clarity_score", 0)
    market_strength = deal.get("market_strength_score", 0)

    score += min(seller_motivation, 20)
    score += min(spread_margin, 20)
    score += min(arv_confidence, 15)
    score += min(repair_confidence, 15)
    score += min(buyer_demand, 15)
    score += min(legal_clarity, 10)
    score += min(market_strength, 5)

    score = max(0, min(score, 100))

    if score >= 85:
        band = "strong_candidate_but_still_requires_human_approval"
    elif score >= 70:
        band = "possible_candidate_needs_more_due_diligence"
    elif score >= 50:
        band = "weak_candidate_high_caution"
    else:
        band = "reject_or_hold"

    return {
        "deal_score": score,
        "recommendation_band": band,
    }


def underwrite_deal(deal: Dict[str, Any]) -> Dict[str, Any]:
    missing_data = detect_missing_data(deal)
    red_flags = detect_red_flags(deal)
    scoring = score_deal(deal)

    arv = float(deal.get("arv", 0) or 0)
    repairs = float(deal.get("repairs", 0) or 0)
    purchase_price = float(deal.get("purchase_price", 0) or 0)

    mao = calculate_mao(
        arv=arv,
        repairs=repairs,
        assignment_fee=float(deal.get("assignment_fee", 15000)),
        safety_buffer=float(deal.get("safety_buffer", 10000)),
    )

    projected_spread = None
    if deal.get("buyer_price"):
        projected_spread = calculate_wholesale_spread(
            contract_price=purchase_price,
            buyer_price=float(deal["buyer_price"]),
        )

    hard_stop_flags = [
        "seller_authority_unverified",
        "arv_not_supported",
        "buyer_demand_missing",
        "legal_review_required_but_not_complete",
        "numbers_only_work_best_case",
        "title_issue_unresolved",
    ]

    hard_stop = any(flag in red_flags for flag in hard_stop_flags)

    if hard_stop:
        recommendation = "PASS_OR_HOLD"
        reason = "Critical red flag detected. Human/legal review required before proceeding."
    elif missing_data:
        recommendation = "HOLD"
        reason = "Missing required data. Do not proceed until completed."
    elif purchase_price > mao:
        recommendation = "RENEGOTIATE_OR_PASS"
        reason = "Purchase price exceeds Heimdall MAO."
    elif scoring["deal_score"] >= 85:
        recommendation = "STRONG_CANDIDATE_PENDING_APPROVAL"
        reason = "Numbers and score are strong, but human approval is still required."
    elif scoring["deal_score"] >= 70:
        recommendation = "POSSIBLE_CANDIDATE_MORE_DUE_DILIGENCE"
        reason = "Deal may work but needs more verification."
    else:
        recommendation = "PASS_OR_HOLD"
        reason = "Deal score is too weak for safe execution."

    return {
        "recommendation": recommendation,
        "reason": reason,
        "mao": mao,
        "purchase_price": purchase_price,
        "projected_spread": projected_spread,
        "deal_score": scoring["deal_score"],
        "recommendation_band": scoring["recommendation_band"],
        "missing_data": missing_data,
        "red_flags": red_flags,
        "human_approval_required": True,
    }
