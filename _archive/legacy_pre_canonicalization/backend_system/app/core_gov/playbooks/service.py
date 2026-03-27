from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(name: str, category: str, region: str = "", steps: List[str] = None, checklist: List[str] = None, notes: str = "", meta: Dict[str, Any] = None, status: str = "active") -> Dict[str, Any]:
    steps = steps or []
    checklist = checklist or []
    meta = meta or {}
    if not (name or "").strip():
        raise ValueError("name required")
    if not (category or "").strip():
        raise ValueError("category required")

    rec = {
        "id": "pbk_" + uuid.uuid4().hex[:12],
        "name": name.strip(),
        "category": category.strip(),   # legal/banking/funding/deals/ops
        "region": (region or "").strip().upper(),  # CA, US, MB, ON, FL...
        "steps": steps,
        "checklist": checklist,
        "notes": notes or "",
        "meta": meta,
        "status": status,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def seed_defaults() -> Dict[str, Any]:
    # light seed set — you can expand later.
    defaults = [
        {
            "name": "Assignment Deal Proof Pack",
            "category": "deals",
            "region": "US",
            "steps": ["Confirm assignment is allowed for this deal", "Collect signed PSA", "Collect assignment agreement", "Collect disclosure (if applicable)", "Build buyer packet"],
            "checklist": ["PSA signed", "Assignment agreement", "Seller disclosures", "Photos", "Repair estimate", "Comps summary"],
        },
        {
            "name": "Canadian Business Bank KYC Pack",
            "category": "banking",
            "region": "CA",
            "steps": ["Choose bank", "Prepare incorporation docs", "Prepare director IDs", "Bring proof of address", "Open account + set alerts"],
            "checklist": ["Articles", "Certificate", "Director ID", "Address proof", "Initial deposit"],
        },
    ]
    created = 0
    for d in defaults:
        create(**d, notes="Seeded default", meta={"seed": True})
        created += 1
    return {"seeded": created}

def list_items(status: str = "", category: str = "", region: str = "", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if category:
        items = [x for x in items if x.get("category") == category]
    if region:
        rr = region.strip().upper()
        items = [x for x in items if (x.get("region") or "") == rr]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("name","").lower()) or qq in (x.get("notes","").lower())]
    items.sort(key=lambda x: (x.get("category",""), x.get("name","")))
    return items[:1000]
