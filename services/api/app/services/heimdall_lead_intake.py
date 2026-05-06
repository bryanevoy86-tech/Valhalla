"""
Heimdall lead intake service - score VA leads and build lead records.
"""

from uuid import uuid4
from datetime import datetime, timezone


DISTRESS_WORDS = [
    "must sell",
    "as is",
    "estate",
    "vacant",
    "foreclosure",
    "tax sale",
    "behind payments",
    "fire damage",
    "water damage",
    "needs work",
    "handyman",
    "fixer",
    "motivated",
    "quick possession",
    "tenant problem",
    "landlord tired",
]


def score_lead(payload: dict) -> dict:
    """Score a VA lead using Heimdall logic."""
    raw = (payload.get("raw_text") or "").lower()
    notes = (payload.get("va_notes") or "").lower()

    score = 40
    reasons = []

    if payload.get("address"):
        score += 15
        reasons.append("Address provided.")
    else:
        score -= 10
        reasons.append("Missing address.")

    if payload.get("asking_price"):
        score += 10
        reasons.append("Asking price provided.")
    else:
        score -= 5
        reasons.append("Missing asking price.")

    if payload.get("seller_phone") or payload.get("seller_email"):
        score += 15
        reasons.append("Seller contact available.")
    else:
        score -= 15
        reasons.append("Missing seller contact.")

    if any(word in raw or word in notes for word in DISTRESS_WORDS):
        score += 25
        reasons.append("Distress or motivation signal detected.")

    if payload.get("source_url"):
        score += 5
        reasons.append("Source URL provided.")

    source_platform = (payload.get("source_platform") or "").lower()
    if source_platform in ["facebook", "kijiji", "google_maps", "city_site", "referral"]:
        score += 5
        reasons.append("Recognized lead source.")

    score = max(0, min(score, 100))

    if score >= 75:
        risk_level = "medium"
        action = "Queue seller contact for Bryan approval"
        next_stage = "approval_required"
        lead_status = "qualified_pending_approval"
    elif score >= 55:
        risk_level = "medium"
        action = "Research more before seller contact"
        next_stage = "needs_research"
        lead_status = "research_required"
    else:
        risk_level = "high"
        action = "Park or reject unless more information is found"
        next_stage = "parked"
        lead_status = "parked"

    return {
        "lead_id": str(uuid4()),
        "lead_status": lead_status,
        "source_platform": payload.get("source_platform"),
        "heimdall_score": score,
        "risk_level": risk_level,
        "confidence": round(score / 100, 2),
        "recommended_action": action,
        "approval_required": True,
        "next_pipeline_stage": next_stage,
        "reasoning_summary": " ".join(reasons),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def build_lead_record(payload: dict, analysis: dict) -> dict:
    """Build a complete lead record from VA intake payload and analysis.
    
    Only includes fields that exist in the VALead model.
    """
    return {
        "source_platform": payload.get("source_platform"),
        "source_type": payload.get("source_type"),
        "source_url": payload.get("source_url"),
        "address": payload.get("address"),
        "city": payload.get("city"),
        "province": payload.get("province"),
        "seller_name": payload.get("seller_name"),
        "seller_phone": payload.get("seller_phone"),
        "seller_email": payload.get("seller_email"),
        "asking_price": payload.get("asking_price"),
        "raw_text": payload.get("raw_text"),
        "va_notes": payload.get("va_notes"),
        "strategy_fit": payload.get("strategy_fit"),
        "submitted_by": payload.get("submitted_by"),
        "heimdall_score": analysis["heimdall_score"],
        "risk_level": analysis["risk_level"],
        "confidence": analysis["confidence"],
        "recommended_action": analysis["recommended_action"],
        "status": analysis["lead_status"],
        "stage": analysis["next_pipeline_stage"],
    }
