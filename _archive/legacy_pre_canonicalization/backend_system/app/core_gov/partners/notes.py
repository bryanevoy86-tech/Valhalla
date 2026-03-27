from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "partners")
PATH = os.path.join(DATA_DIR, "notes.json")

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)

def add(partner_id: str, text: str) -> Dict[str, Any]:
    _ensure()
    rec = {"id":"pnt_" + uuid.uuid4().hex[:12], "partner_id": partner_id, "text": text or "", "at": _utcnow_iso()}
    with open(PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", [])
    items.append(rec)
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items[-50000:]}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
    return rec

def list_notes(partner_id: str = "", limit: int = 50) -> List[Dict[str, Any]]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        items = json.load(f).get("items", [])
    if partner_id:
        items = [x for x in items if x.get("partner_id") == partner_id]
    items.sort(key=lambda x: x.get("at",""), reverse=True)
    return items[:max(1, min(2000, int(limit or 50)))]
