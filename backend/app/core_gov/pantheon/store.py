from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

DATA_DIR = os.path.join("backend", "data", "pantheon")
STATE_PATH = os.path.join(DATA_DIR, "state.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(STATE_PATH):
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(
                {"updated_at": _utcnow_iso(), "state": {"mode": "explore", "reason": "", "last_set_at": _utcnow_iso(), "last_set_by": "seed"}},
                f,
                indent=2,
            )


def read_state() -> Dict[str, Any]:
    _ensure()
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("state", {})


def write_state(state: Dict[str, Any]) -> None:
    _ensure()
    data = {"updated_at": _utcnow_iso(), "state": state}
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, STATE_PATH)
