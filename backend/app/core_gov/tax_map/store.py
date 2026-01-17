"""P-TAXMAP-1: Tax Bucket mapping storage."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

PATH = "backend/data/tax_map/map.json"

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure_dir():
    os.makedirs(os.path.dirname(PATH), exist_ok=True)

def get_map() -> Dict[str, str]:
    """Get current category → bucket mapping."""
    _ensure_dir()
    if not os.path.exists(PATH):
        return {}
    try:
        with open(PATH) as f:
            data = json.load(f)
        return data.get("map", {})
    except:
        return {}

def save_map(m: Dict[str, str]) -> None:
    """Save category → bucket mapping."""
    _ensure_dir()
    tmp = PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"updated_at": _utcnow_iso(), "map": m}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
