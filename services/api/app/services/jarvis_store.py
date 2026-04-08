from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STORE_PATH = Path("var/heimdall_contacts.json")


def _ensure_store() -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        STORE_PATH.write_text('{"contacts": []}', encoding="utf-8")


def load_contacts() -> list[dict[str, Any]]:
    _ensure_store()
    data = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    return data.get("contacts", [])


def save_contacts(contacts: list[dict[str, Any]]) -> None:
    _ensure_store()
    STORE_PATH.write_text(
        json.dumps({"contacts": contacts}, indent=2),
        encoding="utf-8",
    )


def get_contact(contact_id: int) -> dict[str, Any] | None:
    contacts = load_contacts()
    return next((c for c in contacts if c["id"] == contact_id), None)


def update_contact(contact_id: int, updates: dict[str, Any]) -> dict[str, Any] | None:
    contacts = load_contacts()
    updated_contact = None

    for idx, contact in enumerate(contacts):
        if contact["id"] == contact_id:
            contact.update(updates)
            contacts[idx] = contact
            updated_contact = contact
            break

    if updated_contact is not None:
        save_contacts(contacts)

    return updated_contact


def mark_actioned(contact_id: int, action_type: str) -> dict[str, Any] | None:
    contacts = load_contacts()
    updated_contact = None

    for idx, contact in enumerate(contacts):
        if contact["id"] == contact_id:
            contact["last_action_at"] = datetime.now(timezone.utc).isoformat()
            contact["last_action_type"] = action_type
            contact["action_count"] = int(contact.get("action_count", 0)) + 1
            contact["days_stale"] = 0
            contact["status"] = "actioned"
            contacts[idx] = contact
            updated_contact = contact
            break

    if updated_contact is not None:
        save_contacts(contacts)

    return updated_contact
