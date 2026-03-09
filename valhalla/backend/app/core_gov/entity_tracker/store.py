from __future__ import annotations

import json, os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "entity_tracker")
ENTITIES = os.path.join(DATA_DIR, "entities.json")
TASKS = os.path.join(DATA_DIR, "tasks.json")

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    for p in (ENTITIES, TASKS):
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)

def list_entities() -> List[Dict[str, Any]]:
    _ensure()
    with open(ENTITIES, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])

def save_entities(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = ENTITIES + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, ENTITIES)

def list_tasks() -> List[Dict[str, Any]]:
    _ensure()
    with open(TASKS, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])

def save_tasks(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = TASKS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, TASKS)
