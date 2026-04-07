"""
Module 73: Deal → Contract Packager
Prepare deal data for contract generation.
"""
from app.deals.offers import build_offer


def package_for_contract(lead: dict, template_code: str = "WHOLESALE_ASSIGNMENT") -> dict:
    """
    Package lead data for contract creation.
    
    Converts lead data to contract merge fields.
    
    Args:
        lead: Lead data dict
            {
                "address": "123 Main St",
                "city": "Denver",
                "state": "CO",
                "asking_price": 250000,
                "arv": 350000,
                "repairs": 30000
            }
        template_code: DocuSign template code
    
    Returns:
        dict: Packaged contract data or rejection
            {
                "ok": bool,
                "template": str,
                "merge_data": dict,
                "offer": dict
            }
    """
    offer = build_offer(lead)
    if not offer["ok"]:
        return {"ok": False, "offer": offer}

    merge_data = {
        "property_address": lead.get("address"),
        "property_city": lead.get("city"),
        "property_state": lead.get("state"),
        "purchase_price": offer["offer_price"],
        "inspection_days": offer["terms"]["inspection_days"],
        "close_days": offer["terms"]["close_days"],
        "earnest_money": offer["terms"]["earnest_money"],
    }

    return {
        "ok": True,
        "template": template_code,
        "merge_data": merge_data,
        "offer": offer,
    }
