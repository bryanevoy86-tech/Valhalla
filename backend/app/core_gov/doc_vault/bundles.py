from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "doc_vault")
BUNDLES = os.path.join(DATA_DIR, "bundles.json")

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(BUNDLES):
        with open(BUNDLES, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "bundles": []}, f, indent=2)

def _new_id() -> str:
    return "bndl_" + uuid.uuid4().hex[:12]

def list_bundles() -> List[Dict[str, Any]]:
    _ensure()
    with open(BUNDLES, "r", encoding="utf-8") as f:
        return json.load(f).get("bundles", [])

def save_bundles(b: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = BUNDLES + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "bundles": b[-10000:]}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, BUNDLES)

def create(name: str, doc_ids: List[str], links: Dict[str, str] | None = None) -> Dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise ValueError("name required")
    rec = {"id": _new_id(), "name": name, "doc_ids": doc_ids or [], "links": links or {}, "created_at": _utcnow_iso()}
    allb = list_bundles()
    allb.append(rec)
    save_bundles(allb)
    return rec

def get(bundle_id: str) -> Dict[str, Any] | None:
    return next((x for x in list_bundles() if x.get("id") == bundle_id), None)
