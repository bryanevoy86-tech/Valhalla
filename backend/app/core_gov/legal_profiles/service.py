from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(jurisdiction: str, country: str = "", kind: str = "province", notes: str = "", rules: Dict[str, Any] = None) -> Dict[str, Any]:
    jurisdiction = (jurisdiction or "").strip()
    if not jurisdiction:
        raise ValueError("jurisdiction required (e.g., MB, ON, FL)")
    rec = {
        "id": "jur_" + uuid.uuid4().hex[:12],
        "jurisdiction": jurisdiction.upper(),
        "country": (country or "").strip().upper(),
        "kind": (kind or "province").strip().lower(),  # province|state|country|city
        "notes": notes or "",
        "rules": rules or {},  # placeholder: licensing, disclosures, assignment limits, etc.
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(country: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if country:
        items = [x for x in items if x.get("country") == country.upper()]
    items.sort(key=lambda x: (x.get("country",""), x.get("jurisdiction","")))
    return items[:2000]

def get_by_code(code: str) -> Optional[Dict[str, Any]]:
    code = (code or "").strip().upper()
    return next((x for x in store.list_items() if x.get("jurisdiction") == code), None)
