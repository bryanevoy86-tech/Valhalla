from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "audit")
LOG_PATH = os.path.join(DATA_DIR, "events.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)


def read_events() -> List[Dict[str, Any]]:
    _ensure()
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])


def append_event(ev: Dict[str, Any], cap: int = 5000) -> None:
    _ensure()
    items = read_events()
    items.append(ev)
    items = items[-cap:]
    tmp = LOG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, LOG_PATH)
