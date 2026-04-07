"""Operations orchestrator - main deal pipeline runner."""
from app.deals.scoring import evaluate_deal
from app.deals.offers import process_offer
from app.realestate.engine import evaluate_deal as evaluate_with_engine
from app.core.runtime_flags import is_live


def run_deal_pipeline(deal: dict) -> dict:
    """
    Run complete deal pipeline.
    
    Flow:
    1. Score deal
    2. Evaluate with real estate engine
    3. Check floor
    4. Issue offer if approved
    5. Create contract
    
    Args:
        deal: Deal dict with payload
    
    Returns:
        Pipeline result with offer and contract
    """
    # Step 1: Score
    evaluation = evaluate_deal(deal)
    
    if evaluation["recommendation"] == "FAIL":
        return {
            "status": "rejected",
            "deal_id": deal.get("id"),
            "reason": "Failed scoring threshold",
            "score": evaluation["score"]
        }
    
    # Step 2: Real estate engine evaluation
    engine_eval = evaluate_with_engine(
        arv=deal.get("payload", {}).get("arv"),
        purchase_price=deal.get("payload", {}).get("purchase_price")
    )
    
    if not engine_eval.get("viable"):
        return {
            "status": "rejected",
            "deal_id": deal.get("id"),
            "reason": "Failed real estate engine evaluation"
        }
    
    # Step 3-5: Issue offer (handles contract creation)
    offer_result = process_offer(deal)
    
    if offer_result.get("status") == "sandbox":
        return offer_result
    
    if offer_result.get("status") == "rejected":
        return offer_result
    
    # Success
    return {
        "status": "completed",
        "deal_id": deal.get("id"),
        "offer": offer_result.get("offer"),
        "contract_id": offer_result.get("contract_id"),
        "score": evaluation["score"]
    }


def process_multiple_deals(deals: list) -> dict:
    """Process multiple deals in batch."""
    results = {
        "total": len(deals),
        "processed": 0,
        "approved": 0,
        "rejected": 0,
        "offers": [],
        "mode": "live" if is_live() else "sandbox"
    }
    
    for deal in deals:
        result = run_deal_pipeline(deal)
        results["processed"] += 1
        
        if result.get("status") in ["completed", "issued"]:
            results["approved"] += 1
            results["offers"].append(result)
        else:
            results["rejected"] += 1
    
    return results
