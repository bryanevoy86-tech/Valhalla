"""
Heimdall Community Adapter
Bridges Heimdall with the real Community service layer.
Normalizes Community contacts into Heimdall's expected shape.
"""
from __future__ import annotations

from typing import Any


def _normalize_contact(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Convert Community-style contact records into Heimdall's expected shape.
    Adjust field mappings here if your Community schema differs.
    """
    return {
        "id": raw.get("id"),
        "name": raw.get("name") or raw.get("full_name") or "Unknown Contact",
        "type": raw.get("type") or raw.get("contact_type") or "lead",
        "heat_score": int(raw.get("heat_score", 0)),
        "days_stale": int(raw.get("days_stale", 0)),
        "consent_sms": bool(raw.get("consent_sms", False)),
        "consent_email": bool(raw.get("consent_email", False)),
        "preferred_channel": raw.get("preferred_channel") or "phone",
        "reason": raw.get("reason") or "No reason supplied.",
        "recommended_script": raw.get("recommended_script")
        or "Follow up and confirm current interest, timing, and next steps.",
        "status": raw.get("status") or "open",
        "last_action_at": raw.get("last_action_at"),
        "last_action_type": raw.get("last_action_type"),
        "action_count": int(raw.get("action_count", 0)),
    }


def load_community_contacts() -> list[dict[str, Any]]:
    """
    Tries to read from the real Community service layer first.
    Update the import path here if your Community service lives elsewhere.
    """
    try:
        # Example expected service function.
        # Change this import if your real function/module name is different.
        from app.services.community_service import list_contacts  # type: ignore
    except Exception:
        return []

    try:
        raw_contacts = list_contacts()
        if not raw_contacts:
            return []
        return [_normalize_contact(item) for item in raw_contacts if item.get("id") is not None]
    except Exception:
        return []
