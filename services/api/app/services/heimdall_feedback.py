"""
Heimdall Feedback & Learning Engine
Tracks channel effectiveness and adjusts recommendations based on outcomes.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STORE = Path("var/heimdall_channel_feedback.json")


def _ensure() -> None:
    """Ensure feedback store exists."""
    STORE.parent.mkdir(parents=True, exist_ok=True)
    if not STORE.exists():
        STORE.write_text('{"channel_feedback": []}', encoding="utf-8")


def load_feedback() -> list[dict[str, Any]]:
    """Load all feedback entries."""
    _ensure()
    data = json.loads(STORE.read_text(encoding="utf-8"))
    return data.get("channel_feedback", [])


def save_feedback(items: list[dict[str, Any]]) -> None:
    """Persist feedback entries to store."""
    STORE.write_text(
        json.dumps({"channel_feedback": items}, indent=2),
        encoding="utf-8",
    )


def record_feedback(
    contact_id: int,
    channel: str,
    result: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """Record feedback about a channel + outcome for a contact."""
    items = load_feedback()

    entry = {
        "contact_id": contact_id,
        "channel": channel,
        "result": result,
        "notes": notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    items.append(entry)
    save_feedback(items)
    return entry


def get_contact_feedback(contact_id: int) -> list[dict[str, Any]]:
    """Get all feedback for a specific contact."""
    return [x for x in load_feedback() if x.get("contact_id") == contact_id]


def get_channel_stats(contact_id: int) -> dict[str, dict[str, int]]:
    """Calculate performance stats for each channel for a contact."""
    stats: dict[str, dict[str, int]] = defaultdict(
        lambda: {"success": 0, "deal": 0, "no_response": 0, "lost": 0, "total": 0}
    )

    for item in get_contact_feedback(contact_id):
        channel = item.get("channel", "unknown")
        result = item.get("result", "unknown")
        stats[channel]["total"] += 1
        if result in stats[channel]:
            stats[channel][result] += 1

    return dict(stats)


def best_channel_for_contact(
    contact_id: int,
    fallback_channel: str,
) -> tuple[str, list[str]]:
    """
    Determine best channel for a contact based on historical feedback.
    Returns (channel, reasons_list).
    """
    stats = get_channel_stats(contact_id)
    reasons: list[str] = []

    if not stats:
        reasons.append("No historical channel feedback yet")
        return fallback_channel, reasons

    best_channel = fallback_channel
    best_score = -999

    for channel, data in stats.items():
        score = 0
        score += data["success"] * 10
        score += data["deal"] * 20
        score -= data["no_response"] * 5
        score -= data["lost"] * 10

        if score > best_score:
            best_score = score
            best_channel = channel

    reasons.append(f"Best channel chosen from historical feedback: {best_channel}")
    return best_channel, reasons
