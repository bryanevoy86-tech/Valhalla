from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone, date
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "routines")
PATH = os.path.join(DATA_DIR, "runs.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow(), "items": []}, f, indent=2)

def new_id() -> str:
    return "run_" + uuid.uuid4().hex[:12]

def list_runs() -> List[Dict[str, Any]]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])

def save_runs(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow(), "items": items[-200000:]}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)

def start(routine_id: str, run_date: str = "") -> Dict[str, Any]:
    run_date = (run_date or date.today().isoformat()).strip()
    rec = {"id": new_id(), "routine_id": routine_id, "run_date": run_date, "done": [], "status": "open", "created_at": _utcnow(), "updated_at": _utcnow()}
    items = list_runs()
    items.append(rec)
    save_runs(items)
    return rec
