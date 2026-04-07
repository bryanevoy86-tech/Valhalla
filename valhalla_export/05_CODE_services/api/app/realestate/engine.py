"""Real estate engine - evaluate deals and issue offers."""
from app.core.runtime_flags import is_live


def evaluate_deal(deal: dict) -> dict:
    """
    Evaluate a real estate deal.
    
    Returns: dict with score, decision, and reasoning
    """
    if not isinstance(deal, dict):
        raise ValueError("Deal must be a dict")
    
    # Extract key metrics
    price = deal.get("price", 0)
    arv = deal.get("arv", 0)  # After Repair Value
    repairs = deal.get("repairs", 0)
    
    if arv == 0:
        return {
            "score": 0,
            "decision": "REJECT",
            "reason": "No ARV provided",
            "recommendation": "Cannot evaluate deal"
        }
    
    # 70% rule: Purchase price should be <= 70% of ARV
    max_offer = arv * 0.70
    acceptable = price <= max_offer
    
    # Calculate potential profit
    profit = arv - price - repairs
    profit_margin = (profit / arv * 100) if arv > 0 else 0
    
    return {
        "score": profit_margin,
        "decision": "ACCEPT" if acceptable else "REJECT",
        "max_offer": max_offer,
        "estimated_profit": profit,
        "profit_margin_percent": profit_margin,
        "reason": f"Deal at {(price/arv*100):.1f}% of ARV with {profit_margin:.1f}% margin"
    }


def issue_offer(deal: dict, discount: float = 0.9) -> dict:
    """
    Issue an offer for a deal.
    
    Only allowed if system is LIVE.
    
    Args:
        deal: Deal dict with price, arv, repairs
        discount: Offer as % of max acceptable (default 90% to build cushion)
    """
    evaluation = evaluate_deal(deal)
    
    if evaluation["decision"] == "REJECT":
        return {
            "status": "rejected",
            "reason": evaluation["reason"],
            "message": "Cannot issue offer for rejected deal"
        }
    
    if not is_live():
        return {
            "status": "sandbox",
            "deal": deal,
            "offer_price": evaluation["max_offer"] * discount,
            "message": "Sandbox mode - no real offer"
        }
    
    # In LIVE mode, actually issue the offer
    arv = deal.get("arv", 0)
    max_offer = arv * 0.70
    offer_price = max_offer * discount
    
    return {
        "status": "live",
        "offer_id": f"ofr_{__import__('uuid').uuid4().hex[:12]}",
        "offer_price": offer_price,
        "max_price": max_offer,
        "deal_id": deal.get("id"),
        "evaluation": evaluation,
        "message": "Offer issued"
    }


def get_deal_score(deal: dict) -> float:
    """Get a numeric score for a deal (0-100)."""
    evaluation = evaluate_deal(deal)
    return max(0, min(100, evaluation["score"]))
