from __future__ import annotations
import json, os
from datetime import datetime, timezone
from typing import Any, Dict

DATA_DIR = os.path.join("backend", "data", "legal_rules")
PATH = os.path.join(DATA_DIR, "rules.json")

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# v1 DSL: rules = [{"id":"r1","when":{"field":"seller_occupied","eq":True},"flag":{"code":"SELLER_OCCUPIED_NOTICE","level":"warning","msg":"Confirm notice periods"}}]
DEFAULT = {"updated_at": "", "rulesets": {"v1": []}}

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        d = dict(DEFAULT); d["updated_at"] = _utcnow_iso()
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)

def get() -> Dict[str, Any]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save(patch: Dict[str, Any]) -> Dict[str, Any]:
    d = get()
    patch = patch or {}
    if "rulesets" in patch and isinstance(patch["rulesets"], dict):
        d["rulesets"] = patch["rulesets"]
    d["updated_at"] = _utcnow_iso()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
    return d
