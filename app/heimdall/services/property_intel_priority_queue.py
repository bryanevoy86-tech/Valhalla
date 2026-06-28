"""
Property Intel Priority Queue Service

Ranks properties by research priority. VAs work highest-priority leads first.
"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.heimdall.models.property_intel import HeimdallPropertyIntel


def calculate_property_priority_score(record: HeimdallPropertyIntel) -> Dict[str, Any]:
    """
    Calculate priority score (0-100) for a property based on:
    1. Distress score (0-50 max)
    2. Property signals: vacant/boarded, tax arrears, absentee owner (10 points each)
    3. Readiness: outreach allowed, ownership verified (10 points each)
    4. Status-based blocking: certain statuses = score 0

    Returns priority band: URGENT_RESEARCH | HIGH_PRIORITY | MEDIUM_PRIORITY | LOW_PRIORITY | DO_NOT_WORK_NOW
    """
    score = 0
    reasons = []

    # Base score: distress signal (cap at 50)
    distress_score = record.distress_score or 0
    score += min(distress_score, 50)
    if distress_score > 0:
        reasons.append(f"Distress score: {distress_score}")

    # Lead lane bonus
    if record.lead_lane == "HIGH_PRIORITY_RESEARCH_AND_OUTREACH":
        score += 20
        reasons.append("High distress lane")

    # Outreach readiness
    if record.outreach_allowed:
        score += 10
        reasons.append("Outreach currently allowed")

    # Ownership verification
    if record.ownership_verified:
        score += 10
        reasons.append("Ownership verified")

    # Property data signals
    property_data = record.property_data or {}

    if property_data.get("vacant_or_boarded"):
        score += 10
        reasons.append("Vacant or boarded signal")

    if property_data.get("tax_arrears_known"):
        score += 10
        reasons.append("Tax arrears signal")

    if property_data.get("out_of_area_owner"):
        score += 5
        reasons.append("Possible absentee owner")

    # Status-based blocking: these should not be worked on
    if record.research_status in ["DO_NOT_CONTACT", "OUTREACH_BLOCKED", "CONVERTED_TO_LEAD"]:
        score = 0
        reasons = ["Blocked or already converted"]

    # Normalize score to 0-100
    score = max(0, min(score, 100))

    # Assign priority band
    if score >= 80:
        priority_band = "URGENT_RESEARCH"
    elif score >= 60:
        priority_band = "HIGH_PRIORITY"
    elif score >= 40:
        priority_band = "MEDIUM_PRIORITY"
    elif score >= 20:
        priority_band = "LOW_PRIORITY"
    else:
        priority_band = "DO_NOT_WORK_NOW"

    return {
        "property_intel_id": record.id,
        "address": record.address,
        "city": record.city,
        "research_status": record.research_status,
        "distress_score": distress_score,
        "priority_score": score,
        "priority_band": priority_band,
        "reasons": reasons,
    }


def get_property_priority_queue(db: Session) -> Dict[str, Any]:
    """
    Get all properties ranked by priority for research.
    Returns sorted list with highest priority first.
    """
    records = db.query(HeimdallPropertyIntel).all()

    scored = [calculate_property_priority_score(record) for record in records]
    ranked = sorted(scored, key=lambda item: item["priority_score"], reverse=True)

    return {
        "count": len(ranked),
        "priority_queue": ranked,
        "top_property": ranked[0] if ranked else None,
    }
