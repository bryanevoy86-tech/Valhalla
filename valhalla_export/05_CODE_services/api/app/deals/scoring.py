"""
Module 71: Wholesale Scoring Engine
Calculate MAO (Max Allowable Offer) and score leads for viability.
"""


def mao(arv: int, repairs: int, assignment_fee: int = 15000, mao_pct: float = 0.70) -> int:
    """
    Calculate Max Allowable Offer.
    
    Formula: MAO = (ARV * percentage) - repairs - assignment_fee
    
    Args:
        arv: After Repair Value
        repairs: Estimated repair costs
        assignment_fee: Wholesale assignment fee (default 15000)
        mao_pct: MAO percentage of ARV (default 0.70 = 70%)
    
    Returns:
        int: Maximum allowable offer price in cents
    """
    return int((arv * mao_pct) - repairs - assignment_fee)


def score_lead(lead: dict) -> dict:
    """
    Score a deal lead for viability.
    
    Grades:
    - A: Spread >= $25,000
    - B: Spread >= $15,000
    - C: Spread >= $5,000
    - PASS: Below spread threshold
    
    Args:
        lead: Lead data dict
            {
                "arv": 350000,
                "repairs": 30000,
                "asking_price": 250000
            }
    
    Returns:
        dict: Score result
            {
                "mao": int,
                "spread": int,
                "grade": str,
                "ok_to_offer": bool
            }
    """
    arv = lead.get("arv") or 0
    repairs = lead.get("repairs") or 0
    asking = lead.get("asking_price") or 0

    lead_mao = mao(arv, repairs)
    spread = lead_mao - asking

    grade = "PASS"
    if arv > 0 and asking > 0:
        if spread >= 25000:
            grade = "A"
        elif spread >= 15000:
            grade = "B"
        elif spread >= 5000:
            grade = "C"
        else:
            grade = "PASS"

    return {
        "mao": lead_mao,
        "spread": spread,
        "grade": grade,
        "ok_to_offer": grade in {"A", "B", "C"},
    }


def score_deal(deal: dict) -> float:
    """
    Score a deal based on investment metrics.
    
    Uses 70% ARV rule:
    - Acceptable Offer Price = ARV * 0.70 - Repairs
    - Score 0-100 based on margin
    
    Args:
        deal: Deal dict with arv, purchase_price, estimated_repairs
    
    Returns:
        Score 0-100
    """
    arv = deal.get("payload", {}).get("arv", 0)
    purchase_price = deal.get("payload", {}).get("purchase_price", 0)
    repairs = deal.get("payload", {}).get("estimated_repairs", 0)
    
    if not arv or not purchase_price:
        return 0.0
    
    # Calculate 70% rule
    acceptable_price = (arv * 0.70) - repairs
    margin = acceptable_price - purchase_price
    
    # Score: higher margin = higher score
    # Target margin: 30% of purchase price
    target_margin = purchase_price * 0.30
    
    if target_margin <= 0:
        return 0.0
    
    score = min((margin / target_margin) * 100, 100)
    return max(score, 0)


def evaluate_deal(deal: dict) -> dict:
    """
    Comprehensive deal evaluation.
    
    Returns:
        dict with score, recommendation, metrics
    """
    score = score_deal(deal)
    
    recommendation = "PASS" if score >= 70 else "REVIEW" if score >= 50 else "FAIL"
    
    return {
        "deal_id": deal.get("id"),
        "score": score,
        "recommendation": recommendation,
        "metrics": {
            "roi": score,  # Simplified
            "margin_quality": "good" if score >= 70 else "fair" if score >= 50 else "poor"
        }
    }
