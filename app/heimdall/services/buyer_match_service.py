from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.heimdall.models.buyer import HeimdallBuyer


def calculate_buyer_match_score(
    buyer: HeimdallBuyer,
    deal_payload: Dict[str, Any],
) -> Dict[str, Any]:

    score = 0
    reasons = []

    property_city = (
        deal_payload.get("city")
        or deal_payload.get("market")
        or ""
    ).lower()

    property_type = (
        deal_payload.get("property_type")
        or ""
    ).lower()

    arv = float(deal_payload.get("estimated_arv", 0) or 0)

    target_markets = [
        market.lower()
        for market in (buyer.target_markets or [])
    ]

    property_types = [
        prop.lower()
        for prop in (buyer.property_types or [])
    ]

    if property_city in target_markets:
        score += 30
        reasons.append("Target market match.")

    if property_type in property_types:
        score += 25
        reasons.append("Property type match.")

    buy_box = buyer.buy_box or {}

    try:
        min_price = float(buy_box.get("min_price", 0) or 0)
        max_price = float(buy_box.get("max_price", 999999999) or 999999999)

        if min_price <= arv <= max_price:
            score += 25
            reasons.append("ARV within buyer buy box.")
    except Exception:
        pass

    if buyer.proof_of_funds_verified:
        score += 10
        reasons.append("Proof of funds verified.")

    if buyer.reliability_score == "high":
        score += 10
        reasons.append("High reliability buyer.")

    score = max(0, min(score, 100))

    return {
        "buyer_id": buyer.id,
        "buyer_name": buyer.buyer_name,
        "company_name": buyer.company_name,
        "email": buyer.email,
        "phone": buyer.phone,
        "match_score": score,
        "reasons": reasons,
    }


def match_buyers_to_deal(
    db: Session,
    deal_payload: Dict[str, Any],
) -> Dict[str, Any]:

    buyers = (
        db.query(HeimdallBuyer)
        .filter(HeimdallBuyer.buyer_status == "ACTIVE")
        .all()
    )

    matches = [
        calculate_buyer_match_score(
            buyer,
            deal_payload,
        )
        for buyer in buyers
    ]

    ranked = sorted(
        matches,
        key=lambda item: item["match_score"],
        reverse=True,
    )

    return {
        "deal_payload": deal_payload,
        "buyer_match_count": len(ranked),
        "top_matches": ranked[:20],
    }
