"""Deal scoring module - automated deal evaluation."""


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
