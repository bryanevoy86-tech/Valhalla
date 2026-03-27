from __future__ import annotations
import json, os
from datetime import datetime, timezone
from typing import Any, Dict

DATA_DIR = os.path.join("backend", "data", "trust_status")
PATH = os.path.join(DATA_DIR, "status.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

DEFAULT = {
  "updated_at": "",
  "items": {
    "canada_corp_registered": False,
    "bank_account_opened": False,
    "accounting_system_ready": False,
    "master_trust_panama": False,
    "subtrust_canada": False,
    "subtrust_philippines": False,
    "subtrust_nz": False,
    "subtrust_uae": False,
    "privacy_layering": False,
    "insurance_stack": False
  },
  "notes": ""
}

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        d = dict(DEFAULT); d["updated_at"] = _utcnow()
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)

def get() -> Dict[str, Any]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save(patch: Dict[str, Any]) -> Dict[str, Any]:
    d = get()
    patch = patch or {}
    if "items" in patch and isinstance(patch["items"], dict):
        d["items"].update({str(k): bool(v) for k, v in patch["items"].items()})
    if "notes" in patch:
        d["notes"] = patch["notes"]
    d["updated_at"] = _utcnow()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
    return d
