from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "pipeline")
PATH = os.path.join(DATA_DIR, "runs.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow(), "runs": []}, f, indent=2)

def new_id() -> str:
    return "run_" + uuid.uuid4().hex[:12]

def list_runs() -> List[Dict[str, Any]]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("runs", [])

def save_runs(runs: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow(), "runs": runs[-100000:]}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
