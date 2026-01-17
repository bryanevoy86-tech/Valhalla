from __future__ import annotations
import json, os, secrets
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "share_tokens")
PATH = os.path.join(DATA_DIR, "tokens.json")

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "tokens": []}, f, indent=2)

def list_tokens() -> List[Dict[str, Any]]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("tokens", [])

def save_tokens(tokens: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "tokens": tokens[-10000:]}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)

def new_token() -> str:
    return secrets.token_urlsafe(24)
