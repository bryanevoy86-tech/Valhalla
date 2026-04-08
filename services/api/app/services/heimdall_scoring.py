"""
Heimdall Scoring Engine - Money-First Mode
Prioritizes fastest path to cash over everything else.
"""
from __future__ import annotations

from typing import Any

from app.services.jarvis_rules import JARVIS_RULES


def score_contact(contact: dict[str, Any]) -> dict[str, Any]:
    """
    Score a contact with money-first priorities.
    Focuses on: buyers (fastest cash) + staleness (urgency) + opportunity (never contacted).
    """
    heat_score = int(contact.get("heat_score", 0))
    days_stale = int(contact.get("days_stale", 0))
    action_count = int(contact.get("action_count", 0))
    contact_type = contact.get("type", "lead")
    status = contact.get("status", "open")

    score = heat_score
    reasons: list[str] = []

    # ⚔️ MONEY-FIRST BOOST - Buyers are priority #1
    if contact_type == "buyer":
        score += 25
        reasons.append("Buyer prioritized (fastest path to cash)")

    # Staleness = urgency (contacted long ago = high opportunity)
    if days_stale >= 3:
        boost = min(days_stale * 3, 30)
        score += boost
        reasons.append(f"Stale urgency boost (+{boost})")

    # Never contacted yet = high opportunity
    if action_count == 0:
        score += 10
        reasons.append("No prior action (high opportunity)")

    # Recently actioned = deprioritize
    if status == "actioned":
        score -= 30
        reasons.append("Recently actioned")

    # Closed = not worth time
    if status == "closed":
        score -= 100
        reasons.append("Closed contact")

    # Priority thresholds (higher for money-first)
    priority = "low"
    if score >= 100:
        priority = "high"
    elif score >= 70:
        priority = "medium"

    return {
        "score": score,
        "priority": priority,
        "why": reasons,
    }

