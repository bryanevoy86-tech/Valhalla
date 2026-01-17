from __future__ import annotations

from typing import Any, Dict

from app.core_gov.cone.service import get_cone_state
from app.core_gov.deals.scoring.service import score_deal

def next_action_for_deal(deal: dict[str, Any]) -> dict[str, Any]:
    cone = get_cone_state()
    band = cone.band
    stage = (deal.get("stage") or "new").lower()
    s = score_deal(deal)
    score = s["score"]

    # Base action map
    if band in ("C", "D"):
        # stabilize: only protect pipeline, no scaling
        if stage == "new":
            return {"band": band, "action": "light_contact", "why": "Band is stabilization/survival. Do minimal contact, log details.", "priority": "medium"}
        if stage in ("contacted", "qualified"):
            return {"band": band, "action": "follow_up_light", "why": "Keep pipeline warm, avoid escalation.", "priority": "medium"}
        return {"band": band, "action": "hold", "why": "Band is conservative. Do not escalate this deal now.", "priority": "low"}

    # Band A/B normal/caution
    if stage == "new":
        if score >= 75:
            return {"band": band, "action": "call_now", "why": "High score new lead. Contact immediately.", "priority": "high"}
        return {"band": band, "action": "text_then_call", "why": "Initial outreach with log discipline.", "priority": "medium"}

    if stage == "contacted":
        return {"band": band, "action": "qualify", "why": "Move to qualification checklist.", "priority": "high" if score >= 70 else "medium"}

    if stage == "qualified":
        return {"band": band, "action": "send_offer", "why": "Qualified. Send MAO-based offer and schedule follow-up.", "priority": "high"}

    if stage == "offer_sent":
        return {"band": band, "action": "follow_up_24h", "why": "Offer sent. Follow up in 24h with objection handling.", "priority": "high" if score >= 70 else "medium"}

    if stage == "negotiating":
        return {"band": band, "action": "negotiate", "why": "Active negotiation. Use scripts, stay inside caps.", "priority": "high"}

    return {"band": band, "action": "review", "why": "No mapped action. Review manually.", "priority": "low"}
