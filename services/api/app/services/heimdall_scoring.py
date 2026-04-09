"""
Heimdall Scoring Engine - Money-First Mode with Feedback Learning
Prioritizes fastest path to cash + learns from outcome history.
"""
from __future__ import annotations

from typing import Any

from app.services.jarvis_rules import JARVIS_RULES
from app.services.heimdall_outcomes import load_outcomes


def score_contact(contact: dict[str, Any]) -> dict[str, Any]:
    """
    Score a contact with money-first priorities + outcome feedback.
    Focuses on: buyers (fastest cash) + staleness (urgency) + outcome history.
    """
    heat_score = int(contact.get("heat_score", 0))
    days_stale = int(contact.get("days_stale", 0))
    action_count = int(contact.get("action_count", 0))
    contact_type = contact.get("type", "lead")
    status = contact.get("status", "open")
    contact_id = int(contact.get("id", 0))

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

    # ⚔️ OUTCOME FEEDBACK LAYER - Learn from results
    outcomes = [x for x in load_outcomes() if int(x.get("contact_id", 0)) == contact_id]

    success_count = sum(1 for x in outcomes if x.get("result") in {"success", "deal"})
    no_response_count = sum(1 for x in outcomes if x.get("result") == "no_response")
    lost_count = sum(1 for x in outcomes if x.get("result") == "lost")

    if success_count:
        bonus = success_count * 8
        score += bonus
        reasons.append(f"Positive outcome history (+{bonus})")

    if no_response_count:
        penalty = min(no_response_count * 4, 12)
        score -= penalty
        reasons.append(f"No-response history (-{penalty})")

    if lost_count:
        penalty = min(lost_count * 10, 20)
        score -= penalty
        reasons.append(f"Lost-contact penalty (-{penalty})")

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

