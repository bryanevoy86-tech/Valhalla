from typing import Any, Dict, List


def detect_market_missing_data(market: Dict[str, Any]) -> List[str]:
    required = [
        "city",
        "province_or_state",
        "country",
        "population",
        "median_income",
        "average_rent",
        "vacancy_rate",
        "median_home_price",
        "investor_activity_score",
        "buyer_pool_score",
        "distressed_inventory_score",
        "landlord_tenant_risk_score",
        "economic_stability_score",
    ]

    return [
        key for key in required
        if key not in market or market.get(key) in [None, ""]
    ]


def score_market(market: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scores a market from 0-100 for Valhalla expansion.

    Higher score = stronger market.
    """

    score = 0
    warnings = []

    population = float(market.get("population", 0) or 0)
    vacancy_rate = float(market.get("vacancy_rate", 0) or 0)
    median_home_price = float(market.get("median_home_price", 0) or 0)
    average_rent = float(market.get("average_rent", 0) or 0)

    investor_activity_score = int(market.get("investor_activity_score", 0) or 0)
    buyer_pool_score = int(market.get("buyer_pool_score", 0) or 0)
    distressed_inventory_score = int(market.get("distressed_inventory_score", 0) or 0)
    landlord_tenant_risk_score = int(market.get("landlord_tenant_risk_score", 0) or 0)
    economic_stability_score = int(market.get("economic_stability_score", 0) or 0)

    # Population / deal volume potential: max 15
    if population >= 1_000_000:
        score += 15
    elif population >= 500_000:
        score += 12
    elif population >= 250_000:
        score += 9
    elif population >= 100_000:
        score += 6
    else:
        score += 3
        warnings.append("Small population may limit deal volume.")

    # Rent-to-price rough signal: max 15
    if median_home_price > 0:
        rent_to_price = (average_rent * 12) / median_home_price
    else:
        rent_to_price = 0

    if rent_to_price >= 0.08:
        score += 15
    elif rent_to_price >= 0.06:
        score += 12
    elif rent_to_price >= 0.045:
        score += 8
    elif rent_to_price >= 0.035:
        score += 5
    else:
        score += 2
        warnings.append("Weak rent-to-price ratio may hurt BRRRR/rental viability.")

    # Vacancy: max 10
    if 2 <= vacancy_rate <= 5:
        score += 10
    elif 1 <= vacancy_rate < 2:
        score += 7
    elif 5 < vacancy_rate <= 8:
        score += 6
        warnings.append("Higher vacancy may weaken rental stability.")
    elif vacancy_rate < 1:
        score += 5
        warnings.append("Very low vacancy may indicate tight rental supply but difficult tenant movement.")
    else:
        score += 2
        warnings.append("Vacancy rate is concerning.")

    # Qualitative scored factors
    score += min(investor_activity_score, 15)
    score += min(buyer_pool_score, 15)
    score += min(distressed_inventory_score, 15)

    # Risk scores: higher input means safer/better
    score += min(landlord_tenant_risk_score, 8)
    score += min(economic_stability_score, 7)

    score = max(0, min(score, 100))

    if score >= 85:
        recommendation = "STRONG_MARKET_CANDIDATE"
    elif score >= 70:
        recommendation = "TEST_MARKET_WITH_LIMITED_BUDGET"
    elif score >= 50:
        recommendation = "WATCHLIST_ONLY"
    else:
        recommendation = "DO_NOT_ENTER_YET"

    return {
        "market_score": score,
        "recommendation": recommendation,
        "rent_to_price_ratio": round(rent_to_price, 4),
        "warnings": warnings,
    }


def evaluate_market(market: Dict[str, Any]) -> Dict[str, Any]:
    missing_data = detect_market_missing_data(market)
    scoring = score_market(market)

    expansion_blockers = []

    if missing_data:
        expansion_blockers.append("missing_required_market_data")

    if int(market.get("buyer_pool_score", 0) or 0) < 8:
        expansion_blockers.append("buyer_pool_too_weak")

    if int(market.get("distressed_inventory_score", 0) or 0) < 8:
        expansion_blockers.append("not_enough_distressed_inventory")

    if int(market.get("investor_activity_score", 0) or 0) < 8:
        expansion_blockers.append("investor_activity_too_low")

    if scoring["market_score"] < 70:
        expansion_blockers.append("market_score_below_expansion_threshold")

    if expansion_blockers:
        final_decision = "HOLD_OR_RESEARCH_MORE"
    else:
        final_decision = "APPROVED_FOR_TEST_ZONE"

    return {
        "final_decision": final_decision,
        "missing_data": missing_data,
        "expansion_blockers": expansion_blockers,
        **scoring,
        "human_approval_required": True,
    }
