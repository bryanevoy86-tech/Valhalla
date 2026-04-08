"""
Jarvis Interaction History Service
Tracks all contact interactions for future scoring evolution.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INTERACTIONS_FILE = Path(__file__).parent.parent.parent.parent.parent / "var" / "heimdall_interactions.json"


def _ensure_store() -> None:
    """Create interactions file if missing."""
    INTERACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not INTERACTIONS_FILE.exists():
        INTERACTIONS_FILE.write_text(json.dumps({"interactions": []}, indent=2))


def load_interactions() -> list[dict[str, Any]]:
    """Load all interactions from JSON store."""
    _ensure_store()
    content = INTERACTIONS_FILE.read_text()
    data = json.loads(content)
    return data.get("interactions", [])


def save_interactions(interactions: list[dict[str, Any]]) -> None:
    """Persist interactions list to JSON store."""
    _ensure_store()
    data = {"interactions": interactions}
    INTERACTIONS_FILE.write_text(json.dumps(data, indent=2))


def add_interaction(
    contact_id: int,
    contact_name: str,
    interaction_type: str,
    notes: str = "",
) -> dict[str, Any]:
    """
    Record a new interaction for a contact.
    
    Args:
        contact_id: ID of the contact
        contact_name: Name of the contact
        interaction_type: Type of interaction (email_followup, call, sms, etc.)
        notes: Optional notes about the interaction
    
    Returns:
        The created interaction object
    """
    interactions = load_interactions()
    
    # Generate next ID
    next_id = max([i.get("id", 0) for i in interactions], default=0) + 1
    
    interaction = {
        "id": next_id,
        "contact_id": contact_id,
        "contact_name": contact_name,
        "interaction_type": interaction_type,
        "notes": notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    interactions.append(interaction)
    save_interactions(interactions)
    
    return interaction


def get_contact_interactions(contact_id: int) -> list[dict[str, Any]]:
    """Get all interactions for a specific contact."""
    interactions = load_interactions()
    return [i for i in interactions if i.get("contact_id") == contact_id]


def get_recent_interactions(contact_id: int, limit: int = 5) -> list[dict[str, Any]]:
    """Get recent interactions for a contact, limited by count."""
    interactions = get_contact_interactions(contact_id)
    return sorted(
        interactions,
        key=lambda x: x.get("created_at", ""),
        reverse=True,
    )[:limit]
