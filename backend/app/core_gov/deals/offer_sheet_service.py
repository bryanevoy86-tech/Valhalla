from __future__ import annotations

from typing import Any, Dict

from app.core_gov.cone.service import get_cone_state
from app.core_gov.deals.scoring.service import score_deal

def _currency(country: str) -> str:
    return "CAD" if (country or "").upper() == "CA" else "USD"

def build_offer_sheet(deal: dict[str, Any]) -> dict[str, Any]:
    cone = get_cone_state()
    band = cone.band

    s = score_deal(deal)
    score = s["score"]
    mao = float(s["mao_suggested"] or 0.0)

    ask = float(deal.get("asking_price") or 0.0)
    arv = float(deal.get("arv") or 0.0)
    rep = float(deal.get("est_repairs") or 0.0)

    country = (deal.get("country") or "CA").upper()
    cur = _currency(country)

    strategy = (deal.get("strategy") or "wholesale").lower()
    motivation = (deal.get("seller_motivation") or "unknown").lower()
    stage = (deal.get("stage") or "new").lower()

    # Offer ranges (light heuristics; tune later)
    # Range is centered around MAO but respects asking when appropriate
    low_offer = max(0.0, mao * 0.92)
    target_offer = mao
    high_offer = mao * 1.03

    # If ask is already below MAO, you can anchor closer to ask
    if ask > 0 and ask < mao:
        low_offer = max(0.0, ask * 0.95)
        target_offer = min(mao, ask)
        high_offer = min(mao * 1.03, ask * 1.02)

    # Terms
    earnest = 500 if country == "CA" else 1000
    close_days = 14 if motivation == "high" else 21
    inspection_days = 7

    # Band restrictions
    restrictions = []
    if band in ("C", "D"):
        restrictions.append("Cone band is Stabilization/Survival: do not escalate. Use light contact + data gathering only.")
    elif band == "B" and strategy in ("fx_arbitrage", "sports", "collectibles"):
        restrictions.append("Cone band is Caution: opportunistic engines cannot scale (not relevant for deals).")

    # Seller angle (simple v1)
    if motivation == "high":
        seller_angle = "Speed + certainty. Emphasize clean close, less hassle, flexible timeline."
    elif motivation == "medium":
        seller_angle = "Certainty + convenience. Emphasize solutions, options, painless process."
    else:
        seller_angle = "Information + rapport. Ask questions, qualify gently, avoid pushing."

    # Objections playbook (v1)
    objections = [
        {"objection": "Your offer is too low", "response": "I'm pricing in repairs/holding costs and risk. If we confirm repair scope together, I can revisit numbers."},
        {"objection": "I need to think", "response": "Totally fair. What's the main thing you need clarity on—price, timeline, or process? I'll answer that and give you space."},
        {"objection": "Someone else offered more", "response": "That may be true. My advantage is certainty and speed. If they can't close, I can. Do you want a guaranteed close or a maybe?"}
    ]

    # Follow-up cadence (v1)
    cadence = []
    if band in ("C","D"):
        cadence = [
            {"when": "today", "action": "light_contact", "note": "Confirm basics. No pressure."},
            {"when": "48h", "action": "follow_up_light", "note": "Ask if any questions. Keep warm."},
        ]
    else:
        cadence = [
            {"when": "today", "action": "call_or_text", "note": "Confirm motivation, timeline, condition."},
            {"when": "24h", "action": "follow_up", "note": "Re-ask decision blocker; offer solution."},
            {"when": "72h", "action": "follow_up", "note": "Schedule walkthrough / collect photos / finalize offer."},
            {"when": "7d", "action": "nurture", "note": "Soft touch. Keep relationship."},
        ]

    # Disposition notes for wholesale (v1)
    disposition = {}
    if strategy == "wholesale":
        disposition = {
            "buyer_type": "cash/investor",
            "package_needed": ["address (if available)", "photos", "repair estimate", "ARV comps summary", "access window"],
            "disclaimer": "Do not market as MLS. Use compliant language and assignable contract rules.",
        }

    return {
        "deal_id": deal.get("id"),
        "band": band,
        "currency": cur,
        "inputs": {
            "asking_price": ask or None,
            "arv": arv or None,
            "est_repairs": rep or None,
            "strategy": strategy,
            "seller_motivation": motivation,
            "stage": stage,
        },
        "score": s,
        "offer_guidance": {
            "low_offer": round(low_offer, 2),
            "target_offer": round(target_offer, 2),
            "high_offer": round(high_offer, 2),
            "earnest_money": earnest,
            "inspection_days": inspection_days,
            "close_days_target": close_days,
        },
        "seller_angle": seller_angle,
        "objections": objections,
        "follow_up_cadence": cadence,
        "disposition": disposition,
        "restrictions": restrictions,
        "notes": [
            "Offer sheet is advisory only; you approve final numbers and terms.",
            "Tune MAO heuristics per province/state later (KV + underwriting packs).",
        ],
    }
