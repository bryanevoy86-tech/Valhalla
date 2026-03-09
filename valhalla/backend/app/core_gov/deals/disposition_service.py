from __future__ import annotations

from typing import Any, Dict

from app.core_gov.deals.scoring.service import score_deal
from app.core_gov.deals.next_action.service import next_action_for_deal
from app.core_gov.deals.offer_sheet_service import build_offer_sheet
from app.core_gov.deals.scripts_service import build_scripts
from app.core_gov.buyers.match import match_buyers_to_deal

def build_disposition_package(deal: dict[str, Any], buyer_limit: int = 10) -> dict[str, Any]:
    country = (deal.get("country") or "CA").upper()
    strategy = (deal.get("strategy") or "wholesale").lower()

    score = score_deal(deal)
    nxt = next_action_for_deal(deal)
    offer = build_offer_sheet(deal)

    scripts = {
        "text": build_scripts(deal, channel="text"),
        "email": build_scripts(deal, channel="email"),
    }

    buyer_matches = []
    if strategy == "wholesale":
        buyer_matches = match_buyers_to_deal(deal, limit=buyer_limit)

    # clean presentation summary
    summary = {
        "location": {
            "country": country,
            "province_state": deal.get("province_state"),
            "city": deal.get("city"),
            "address": deal.get("address"),
            "postal_zip": deal.get("postal_zip"),
        },
        "property": {
            "property_type": deal.get("property_type"),
            "beds": deal.get("bedrooms"),
            "baths": deal.get("bathrooms"),
            "sqft": deal.get("sqft"),
        },
        "strategy": strategy,
        "pipeline": {
            "stage": deal.get("stage"),
            "lead_source": deal.get("lead_source"),
            "seller_motivation": deal.get("seller_motivation"),
            "seller_reason": deal.get("seller_reason"),
            "timeline_days": deal.get("timeline_days"),
        },
        "numbers": {
            "asking_price": deal.get("asking_price"),
            "arv": deal.get("arv"),
            "est_repairs": deal.get("est_repairs"),
            "mao_current": deal.get("mao"),
            "mao_suggested": score.get("mao_suggested"),
            "equity_pct": score.get("equity_pct"),
            "est_rent_monthly": deal.get("est_rent_monthly"),
        },
        "tags": deal.get("tags") or [],
        "notes": deal.get("notes"),
    }

    compliance = [
        "This package is informational and for internal use.",
        "Ensure your marketing/disposition method complies with your local laws, assignment rules, and advertising requirements.",
        "Do not represent estimates as guarantees. Verify condition, title, and access terms.",
        "If using email/text campaigns, comply with anti-spam rules for your jurisdiction.",
    ]

    if strategy == "wholesale":
        compliance.append("For wholesale: verify assignment/novation legality and use compliant contract language.")

    return {
        "deal_id": deal.get("id"),
        "created_at_utc": deal.get("created_at_utc"),
        "updated_at_utc": deal.get("updated_at_utc"),
        "summary": summary,
        "score": score,
        "next_action": nxt,
        "offer_sheet": offer,
        "buyer_matches": buyer_matches,
        "scripts": scripts,
        "compliance_notes": compliance,
        "export_hint": {
            "recommended_fields": [
                "deal_id",
                "summary.location",
                "summary.property",
                "summary.numbers",
                "score",
                "offer_sheet.offer_guidance",
                "buyer_matches",
                "scripts.text.opener",
                "scripts.email.opener",
            ],
            "use_case": "WeWeb can render this directly as a Disposition Packet page.",
        },
    }
