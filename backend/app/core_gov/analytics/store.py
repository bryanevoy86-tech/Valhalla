from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "analytics")
HISTORY_PATH = os.path.join(DATA_DIR, "history.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)


def read_history() -> List[Dict[str, Any]]:
    _ensure()
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])


def append_snapshot(snap: Dict[str, Any]) -> None:
    _ensure()
    items = read_history()
    items.append(snap)
    data = {"updated_at": _utcnow_iso(), "items": items[-2000:]}  # cap growth
    tmp = HISTORY_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, HISTORY_PATH)
