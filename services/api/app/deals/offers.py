"""
Module 72: Offers Generator
Generate purchase offers based on lead scoring and wholesale calculations.
"""
from app.deals.scoring import score_lead


def build_offer(lead: dict) -> dict:
    """
    Generate purchase offer for a lead.
    
    Args:
        lead: Lead data dict
            {
                "asking_price": 250000,
                "arv": 350000,
                "repairs": 30000
            }
    
    Returns:
        dict: Offer details or rejection
            {
                "ok": bool,
                "offer_price": int,
                "terms": {
                    "inspection_days": 10,
                    "close_days": 21,
                    "earnest_money": 1000
                },
                "score": dict
            }
    """
    s = score_lead(lead)
    if not s["ok_to_offer"]:
        return {"ok": False, "reason": "Lead below threshold", "score": s}

    offer_price = min((lead.get("asking_price") or s["mao"]), s["mao"])
    return {
        "ok": True,
        "offer_price": offer_price,
        "terms": {
            "inspection_days": 10,
            "close_days": 21,
            "earnest_money": 1000,
        },
        "score": s,
    }


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
