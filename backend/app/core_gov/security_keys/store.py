from __future__ import annotations
import json, os, secrets
from datetime import datetime, timezone
from typing import Any, Dict

DATA_DIR = os.path.join("backend", "data", "security_keys")
PATH = os.path.join(DATA_DIR, "keys.json")

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "keys": []}, f, indent=2)

def list_keys():
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("keys", [])

def save_keys(keys):
    _ensure()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "keys": keys[-1000:]}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)

def new_key() -> str:
    return secrets.token_urlsafe(32)
