from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "comms")
MSGS_PATH = os.path.join(DATA_DIR, "messages.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(MSGS_PATH):
        with open(MSGS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)


def list_msgs() -> List[Dict[str, Any]]:
    _ensure()
    with open(MSGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])


def save_msgs(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = MSGS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, MSGS_PATH)
