"""Offer issuance pipeline - create and send offers."""
from uuid import uuid4
from app.core.runtime_flags import is_live
from app.deals.scoring import evaluate_deal
from app.contracts.service import create_contract


def process_offer(deal: dict, template_id: str = None) -> dict:
    """
    Process an offer for a deal.
    
    Flow: Score deal → Evaluate → Issue offer → Create contract
    
    Args:
        deal: Deal dict
        template_id: Contract template ID (uses default if None)
    
    Returns:
        dict with offer and contract info
    """
    # Score the deal
    evaluation = evaluate_deal(deal)
    
    if evaluation["recommendation"] == "FAIL":
        return {
            "status": "rejected",
            "reason": "Deal does not meet scoring criteria",
            "score": evaluation["score"]
        }
    
    # Create offer
    offer_id = f"offer_{uuid4().hex[:12]}"
    offer = {
        "id": offer_id,
        "deal_id": deal.get("id"),
        "amount": deal.get("payload", {}).get("purchase_price", 0),
        "score": evaluation["score"],
        "status": "pending"
    }
    
    if not is_live():
        return {
            "status": "sandbox",
            "offer": offer,
            "message": "Offer would be created and sent in live mode"
        }
    
    # Create associated contract
    contract_result = create_contract(
        template_id=template_id or "default",
        merge_data={"deal_id": deal.get("id")}
    )
    
    return {
        "status": "issued",
        "offer": offer,
        "contract_id": contract_result.get("id")
    }


def issue_offer(deal_id: str, amount: float) -> dict:
    """Issue an offer directly (simpler flow)."""
    if not is_live():
        return {
            "status": "sandbox",
            "offer_id": f"offer_{uuid4().hex[:12]}",
            "message": "Offer would be issued in live mode"
        }
    
    return {
        "status": "issued",
        "offer_id": f"offer_{uuid4().hex[:12]}",
        "deal_id": deal_id,
        "amount": amount
    }
