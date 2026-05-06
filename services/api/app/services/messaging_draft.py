"""Seller message drafting service - creates templates only, does not send."""


def draft_seller_message(lead_data: dict, message_type: str = "initial_contact") -> dict:
    """
    Draft a message to send to a seller.
    
    This service ONLY drafts messages.
    It does NOT send them - requires manual approval.
    
    Args:
        lead_data: Lead information dict with address, seller_name, etc.
        message_type: Type of message (initial_contact, follow_up, offer)
    
    Returns:
        dict with draft message and approval requirements
    """
    
    address = lead_data.get("address", "the property")
    seller_name = lead_data.get("seller_name", "Seller")
    asking_price = lead_data.get("asking_price", "asking price")
    city = lead_data.get("city", "")
    province = lead_data.get("province", "")
    
    location = f"{city}, {province}".strip(" ,")
    if location:
        location = f" in {location}"
    
    messages = {
        "initial_contact": f"""Hi {seller_name},

I saw your property at {address}{location} listed at ${asking_price:,}.

We specialize in quick, fair offers for properties like yours. If you're considering options for your home, we'd like to help.

Would you be available for a brief call this week to discuss?

Best regards,
Valhalla Legacy Inc.
""",
        
        "follow_up": f"""Hi {seller_name},

Following up on my previous message about {address}.

We still believe there might be a great opportunity here. Are you open to exploring options?

Let me know your availability.

Best regards,
Valhalla Legacy Inc.
""",
        
        "offer": f"""Hi {seller_name},

We've reviewed {address} and would like to make an offer.

Given the current market and condition, we can move quickly with fair terms.

Available to discuss today if you're interested.

Best regards,
Valhalla Legacy Inc.
"""
    }
    
    draft = messages.get(message_type, messages["initial_contact"])
    
    return {
        "success": True,
        "lead_id": lead_data.get("id"),
        "message_type": message_type,
        "draft": draft,
        "requires_bryan_approval": True,
        "note": "This is a draft only. Do not send without manual review and approval.",
        "instructions": [
            "1. Review draft for accuracy",
            "2. Customize if needed",
            "3. Get Bryan approval",
            "4. Send via approved channel"
        ]
    }


def draft_buyer_packet(deal_data: dict) -> dict:
    """
    Create a buyer information packet from a deal.
    
    This summarizes key deal info for prospective buyers.
    
    Args:
        deal_data: Deal information dict
    
    Returns:
        dict with buyer packet summary
    """
    
    address = deal_data.get("address", "TBD")
    price = deal_data.get("asking_price", deal_data.get("price", 0))
    arv = deal_data.get("arv", price)
    estimated_repairs = deal_data.get("estimated_repairs", 0)
    
    potential_profit = arv - price - estimated_repairs if arv and price else 0
    
    return {
        "success": True,
        "deal_id": deal_data.get("id"),
        "packet": {
            "property": {
                "address": address,
                "city": deal_data.get("city", "TBD"),
                "province": deal_data.get("province", "TBD"),
            },
            "financials": {
                "purchase_price": price,
                "estimated_repairs": estimated_repairs,
                "after_repair_value": arv,
                "estimated_profit": potential_profit,
                "profit_margin": f"{(potential_profit / price * 100):.1f}%" if price > 0 else "N/A"
            },
            "property_info": {
                "type": deal_data.get("property_type", "Single Family"),
                "beds": deal_data.get("beds", "TBD"),
                "baths": deal_data.get("baths", "TBD"),
                "sqft": deal_data.get("sqft", "TBD"),
            },
            "risks": [
                "Verify property condition with inspection",
                "Confirm repair estimates",
                "Check market comparables for ARV",
                "Verify title and liens"
            ],
            "next_steps": [
                "1. Schedule property walkthrough",
                "2. Get inspection estimate",
                "3. Research comparable sales",
                "4. Prepare offer"
            ]
        },
        "note": "This packet is for qualified buyers only. Do not distribute without approval."
    }
