"""
Heimdall Scoring Engine
Provides explainable contact priority scoring.
"""
from __future__ import annotations

from typing import Any

from app.services.jarvis_rules import JARVIS_RULES


def score_contact(contact: dict[str, Any]) -> dict[str, Any]:
    """
    Score a contact and return priority + explanation.
    """
    heat_score = int(contact.get("heat_score", 0))
    days_stale = int(contact.get("days_stale", 0))
    action_count = int(contact.get("action_count", 0))
    contact_type = contact.get("type", "lead")
    status = contact.get("status", "open")

    score = heat_score
    reasons: list[str] = []

    if contact_type == "buyer" and JARVIS_RULES.get("buyer_fast_cash_priority", False):
        score += 15
        reasons.append("Buyer prioritized for faster cash potential")

    if days_stale >= JARVIS_RULES.get("stale_lead_days", 3):
        stale_boost = min(days_stale * 2, 20)
        score += stale_boost
        reasons.append(f"Stale follow-up urgency boost (+{stale_boost})")

    if action_count == 0:
        score += 5
        reasons.append("No actions logged yet")

    if status == "actioned":
        score -= 25
        reasons.append("Recently actioned")

    if status == "closed":
        score -= 100
        reasons.append("Closed contact deprioritized")

    priority = "low"
    if score >= 90:
        priority = "high"
    elif score >= 60:
        priority = "medium"

    return {
        "score": score,
        "priority": priority,
        "why": reasons,
    }
