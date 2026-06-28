from typing import Any, Dict, List


BUYER_SOURCE_REGISTRY = {
    "winnipeg": [
        {
            "name": "Winnipeg Real Estate Wholesale / Off Market Cash Buyers Meetup",
            "source_type": "investor_meetup",
            "url": "https://www.meetup.com/winnipeg-real-estate-investors-network-rei-club/",
            "buyer_types": ["cash_buyer", "flipper", "landlord", "private_lender"],
            "priority": 1,
        },
        {
            "name": "NREIC Open",
            "source_type": "national_investor_community",
            "url": "https://www.nreic.ca/",
            "buyer_types": ["landlord", "flipper", "capital_partner", "jv_partner"],
            "priority": 1,
        },
        {
            "name": "Winnipeg Regional Real Estate Board",
            "source_type": "realtor_network",
            "url": "https://www.winnipegregionalrealestateboard.ca/about-us/who-is-who",
            "buyer_types": ["investor_realtor", "broker_referral", "buyer_agent"],
            "priority": 2,
        },
    ],
    "generic_sources": [
        "real_estate_investor_associations",
        "landlord_associations",
        "cash_buyer_websites",
        "facebook_investor_groups",
        "meetup_rei_groups",
        "biggerpockets_forums",
        "linkedin_investors",
        "public_property_buyer_companies",
        "realtors_with_investor_clients",
        "private_lender_networks",
    ],
}


def generate_buyer_sourcing_plan(city: str, strategy: str) -> Dict[str, Any]:
    city_key = city.lower().strip()
    local_sources = BUYER_SOURCE_REGISTRY.get(city_key, [])

    return {
        "city": city,
        "strategy": strategy,
        "local_sources": local_sources,
        "generic_sources_to_search": BUYER_SOURCE_REGISTRY["generic_sources"],
        "instructions": [
            "Only use public or permission-based contact sources.",
            "Do not scrape private groups without permission.",
            "Do not spam buyers.",
            "Record buyer buy-box before sending deals.",
            "Confirm proof of funds or financing ability before relying on buyer.",
            "Tag buyers by property type, price range, area, rehab tolerance, and close speed.",
        ],
    }


def score_buyer_match(deal: Dict[str, Any], buyer: Dict[str, Any]) -> Dict[str, Any]:
    score = 0
    reasons = []

    if deal.get("city") in buyer.get("target_cities", []):
        score += 20
        reasons.append("Buyer targets this city.")

    if deal.get("property_type") in buyer.get("property_types", []):
        score += 20
        reasons.append("Buyer likes this property type.")

    price = float(deal.get("target_buyer_price", 0) or 0)
    min_price = float(buyer.get("min_price", 0) or 0)
    max_price = float(buyer.get("max_price", 0) or 0)

    if min_price <= price <= max_price:
        score += 20
        reasons.append("Deal price fits buyer range.")

    if deal.get("rehab_level") in buyer.get("rehab_tolerance", []):
        score += 15
        reasons.append("Rehab level fits buyer tolerance.")

    if buyer.get("proof_of_funds_verified", False):
        score += 15
        reasons.append("Proof of funds verified.")

    if buyer.get("close_speed_days", 999) <= deal.get("required_close_days", 30):
        score += 10
        reasons.append("Buyer can close inside required timeline.")

    score = max(0, min(score, 100))

    if score >= 80:
        match_band = "STRONG_MATCH"
    elif score >= 60:
        match_band = "POSSIBLE_MATCH"
    elif score >= 40:
        match_band = "WEAK_MATCH"
    else:
        match_band = "DO_NOT_SEND"

    return {
        "buyer_name": buyer.get("name"),
        "buyer_id": buyer.get("id"),
        "match_score": score,
        "match_band": match_band,
        "reasons": reasons,
    }


def rank_buyers_for_deal(deal: Dict[str, Any], buyers: List[Dict[str, Any]]) -> Dict[str, Any]:
    scored = [score_buyer_match(deal, buyer) for buyer in buyers]
    scored = sorted(scored, key=lambda x: x["match_score"], reverse=True)

    return {
        "deal_id": deal.get("id"),
        "property_address": deal.get("property_address"),
        "ranked_buyers": scored,
        "recommended_send_list": [
            buyer for buyer in scored if buyer["match_score"] >= 60
        ],
        "blocked_buyers": [
            buyer for buyer in scored if buyer["match_score"] < 40
        ],
        "human_approval_required_before_message": True,
    }


def draft_buyer_message(deal: Dict[str, Any], buyer: Dict[str, Any]) -> Dict[str, Any]:
    message = f"""
Hi {buyer.get('name', 'there')},

I have a potential off-market opportunity in {deal.get('city')} that may fit your buy box.

Property: {deal.get('property_address')}
Type: {deal.get('property_type')}
Estimated ARV: ${deal.get('arv'):,.0f}
Projected buyer price: ${deal.get('target_buyer_price'):,.0f}
Estimated repairs: ${deal.get('estimated_repairs'):,.0f}
Rehab level: {deal.get('rehab_level')}

Before I send the full package, does this fit what you are currently buying?

Thanks,
Valhalla Legacy Inc.
""".strip()

    return {
        "buyer_id": buyer.get("id"),
        "buyer_name": buyer.get("name"),
        "message_type": "buyer_interest_check",
        "message": message,
        "requires_approval_before_sending": True,
    }
