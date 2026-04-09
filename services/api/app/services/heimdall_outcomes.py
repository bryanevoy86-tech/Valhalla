"""
Heimdall Outcome Tracking
Records the results of actions taken on contacts.
Separates guessing from learning.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STORE = Path("var/heimdall_outcomes.json")


def _ensure() -> None:
    """Ensure outcomes store exists."""
    STORE.parent.mkdir(parents=True, exist_ok=True)
    if not STORE.exists():
        STORE.write_text('{"outcomes": []}', encoding="utf-8")


def load_outcomes() -> list[dict[str, Any]]:
    """Load all recorded outcomes."""
    _ensure()
    data = json.loads(STORE.read_text(encoding="utf-8"))
    return data.get("outcomes", [])


def save_outcomes(data: list[dict[str, Any]]) -> None:
    """Persist outcomes to store."""
    _ensure()
    STORE.write_text(json.dumps({"outcomes": data}, indent=2), encoding="utf-8")


def record_outcome(
    contact_id: int,
    result: str,
    notes: str | None = None,
    channel: str | None = None,
    task_id: int | None = None,
) -> dict[str, Any]:
    """
    Record outcome of an action on a contact.
    Links to task if provided for closed-loop tracking.
    
    Results: "success", "no_response", "deal", "lost", "other"
    Channel: "sms", "email", "phone", etc.
    """
    outcomes = load_outcomes()

    item = {
        "id": max([o.get("id", 0) for o in outcomes], default=0) + 1,
        "contact_id": contact_id,
        "result": result,
        "notes": notes,
        "channel": channel,
        "task_id": task_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    outcomes.append(item)
    save_outcomes(outcomes)

    return item

    return item


def get_contact_outcomes(contact_id: int) -> list[dict[str, Any]]:
    """Get all outcomes for a specific contact."""
    outcomes = load_outcomes()
    return [o for o in outcomes if o.get("contact_id") == contact_id]
