from __future__ import annotations

from typing import Any, Dict

from app.core_gov.cone.service import get_cone_state
from app.core_gov.deals.scoring.service import score_deal

def build_scripts(deal: dict[str, Any], channel: str = "call") -> dict[str, Any]:
    cone = get_cone_state()
    band = cone.band

    motivation = (deal.get("seller_motivation") or "unknown").lower()
    stage = (deal.get("stage") or "new").lower()
    strategy = (deal.get("strategy") or "wholesale").lower()
    city = deal.get("city") or "your area"

    s = score_deal(deal)
    mao = s.get("mao_suggested")

    # tone rules
    if band in ("C","D"):
        tone = "low-pressure, supportive, data-gathering"
    elif motivation == "high":
        tone = "direct, efficient, certainty-focused"
    else:
        tone = "calm, helpful, conversational"

    opener_call = f"Hey — is this the owner of the property in {city}? I'm calling because I'm looking to buy a home in the area and wanted to see if you'd consider an offer."
    opener_text = f"Hi — I'm looking to buy a home in {city}. Would you consider an offer on your property?"
    opener_email = f"Subject: Quick question about your property in {city}\n\nHi — I'm looking to buy a home in {city} and wanted to ask if you'd consider an offer. If yes, what's the best time to talk?"

    qualify = [
        "What's got you considering a sale right now?",
        "What timeline are you hoping for?",
        "Any major repairs or issues you already know about?",
        "Is there a mortgage or any liens I should be aware of?",
        "If we agreed on a price, what would you need the process to look like for it to be easy?",
    ]

    if band in ("C","D"):
        offer_frame = "I'm not trying to push anything today. If you want, I can ask a few questions and see if it even makes sense to put numbers together."
    else:
        offer_frame = f"Based on similar homes and repairs, I can usually put an offer together pretty quickly. If it helps, I can start around a number and we adjust based on what we confirm."

    if mao:
        offer_frame += f" (My early math puts it roughly in the {round(float(mao),2)} range depending on condition.)"

    objections = [
        {"objection": "Your offer is too low", "reply": "Totally fair. My number is based on repairs + risk + carrying costs. If we verify repair scope together, I can revisit."},
        {"objection": "I need to think about it", "reply": "Of course. What's the one thing you'd need clarity on to decide—price, timeline, or trust in the process?"},
        {"objection": "I'll list with an agent", "reply": "That can be a great option. If you want certainty and speed with less hassle, I'm the alternative. Want to compare both paths?"}
    ]

    cta = "If you're open to it, I can ask a few quick questions now and then I'll send you a clean written offer to review."
    if stage in ("offer_sent","negotiating"):
        cta = "What would need to change for this to be a yes? If it's price or timeline, tell me and I'll see what's possible."

    pack = {
        "band": band,
        "tone": tone,
        "channel": channel,
        "opener": opener_call if channel == "call" else opener_text if channel == "text" else opener_email,
        "qualification_questions": qualify,
        "offer_framing": offer_frame,
        "objections": objections,
        "cta": cta,
        "notes": [
            "Scripts are guidance only. Use lawful compliance in your jurisdiction.",
            "If seller is distressed, stay respectful and avoid pressure tactics.",
        ],
    }
    return pack
