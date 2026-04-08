"""
Community Service Bridge
Temporary bridge to provide Heimdall with live contacts.
Replace this later with real DB/service reads from your Community module.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def list_contacts() -> list[dict[str, Any]]:
    """
    Temporary bridge.
    Replace this later with real DB/service reads from your Community module.
    """
    path = Path("var/heimdall_contacts.json")
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("contacts", [])
