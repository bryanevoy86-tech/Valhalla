from typing import Any, Dict, List


def normalize_score(value: float, max_value: float) -> float:
    """
    Normalize a value to 0-100 scale.
    
    Example: projected_spread of $25,000 on a max of $50,000 = 50 points
    """
    if max_value <= 0:
        return 0
    return max(0, min((value / max_value) * 100, 100))


def calculate_deal_priority_score(deal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate priority score for a single deal.
    
    Weights:
    - Deal score: 25% (underwriting viability)
    - Motivation score: 20% (seller urgency)
    - Buyer demand: 20% (cash buyer interest)
    - Market score: 15% (market conditions)
    - Spread score: 20% (projected profit)
    
    Risk penalties (subtracted from final):
    - Red flag: -8 points each
    - Missing data: -4 points each
    - Lawyer review needed: -10 points
    - Seller authority not verified: -25 points
    - Buyer demand not verified: -20 points
    
    Returns: {priority_score (0-100), priority_band, risk details}
    """

    # Extract component scores
    deal_score = float(deal.get("deal_score", 0) or 0)
    motivation_score = float(deal.get("motivation_score", 0) or 0)
    buyer_demand_score = float(deal.get("buyer_demand_score", 0) or 0)
    market_score = float(deal.get("market_score", 0) or 0)

    # Calculate spread score (0-100 normalized from projected_spread)
    projected_spread = float(deal.get("projected_spread", 0) or 0)
    spread_score = normalize_score(projected_spread, 50000)

    # Calculate risk penalty
    risk_penalty = 0

    red_flags = deal.get("red_flags", [])
    missing_data = deal.get("missing_data", [])

    risk_penalty += len(red_flags) * 8
    risk_penalty += len(missing_data) * 4

    # Major risk penalties
    if deal.get("legal_review_required", True) and not deal.get(
        "lawyer_review_complete", False
    ):
        risk_penalty += 10

    if not deal.get("seller_authority_verified", False):
        risk_penalty += 25

    if not deal.get("buyer_demand_verified", False):
        risk_penalty += 20

    # Calculate weighted score
    weighted_score = (
        (deal_score * 0.25)
        + (motivation_score * 0.20)
        + (buyer_demand_score * 0.20)
        + (market_score * 0.15)
        + (spread_score * 0.20)
    )

    # Final score after risk adjustment
    final_score = max(0, min(weighted_score - risk_penalty, 100))

    # Determine priority band
    if final_score >= 85:
        priority_band = "TOP_PRIORITY"
    elif final_score >= 70:
        priority_band = "HIGH_PRIORITY"
    elif final_score >= 55:
        priority_band = "MEDIUM_PRIORITY"
    elif final_score >= 40:
        priority_band = "LOW_PRIORITY"
    else:
        priority_band = "DO_NOT_PRIORITIZE"

    return {
        "deal_id": deal.get("id"),
        "property_address": deal.get("property_address"),
        "priority_score": round(final_score, 2),
        "priority_band": priority_band,
        "projected_spread": projected_spread,
        "risk_penalty": risk_penalty,
        "red_flags": red_flags,
        "missing_data": missing_data,
    }


def compare_deals(deals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compare multiple deals and rank by priority.
    
    Input: List of deal objects with scores
    Output: Ranked list + top deal + recommendation
    """

    scored = [calculate_deal_priority_score(deal) for deal in deals]
    ranked = sorted(scored, key=lambda x: x["priority_score"], reverse=True)

    return {
        "deal_count": len(deals),
        "ranked_deals": ranked,
        "top_deal": ranked[0] if ranked else None,
        "do_not_prioritize": [
            deal for deal in ranked if deal["priority_band"] == "DO_NOT_PRIORITIZE"
        ],
        "recommendation": build_comparison_recommendation(ranked),
    }


def build_comparison_recommendation(ranked: List[Dict[str, Any]]) -> str:
    """
    Build actionable recommendation based on ranked deals.
    """

    if not ranked:
        return "No deals provided."

    top = ranked[0]

    # If top deal is strong, recommend focusing on it
    if top["priority_band"] in ["TOP_PRIORITY", "HIGH_PRIORITY"]:
        return (
            f"Focus first on {top['property_address']} because it has the strongest "
            f"risk-adjusted opportunity score ({top['priority_score']}/100). "
            f"Projected spread: ${top['projected_spread']:,.0f}."
        )

    # If top deal is medium, suggest improving data
    if top["priority_band"] == "MEDIUM_PRIORITY":
        return (
            "No deal is currently strong enough for aggressive action. "
            "Work the top deal only after missing data and risks are reduced. "
            f"Missing data: {top.get('missing_data', [])}. "
            f"Red flags: {top.get('red_flags', [])}."
        )

    # If top deal is low or do-not-prioritize
    return "No current deal deserves major time or money. Keep sourcing."
