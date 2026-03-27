from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(provider: str, country: str = "CA", steps: List[str] = None, proof_pack: List[str] = None, notes: str = "", status: str = "active", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    steps = steps or []
    proof_pack = proof_pack or []
    meta = meta or {}
    provider = (provider or "").strip()
    if not provider:
        raise ValueError("provider required")

    rec = {
        "id": "apg_" + uuid.uuid4().hex[:12],
        "provider": provider,
        "country": (country or "CA").strip().upper(),
        "steps": steps,
        "proof_pack": proof_pack,
        "notes": notes or "",
        "status": status,
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def seed_defaults() -> Dict[str, Any]:
    defaults = [
        {
            "provider": "Generic Bank Autopay (Bill Payments)",
            "country": "CA",
            "steps": [
                "Log into online banking",
                "Go to Bills / Pay Bills / Bill Payments",
                "Add payee (provider name from bill)",
                "Enter account number from bill",
                "Set recurring payment amount + date (or minimum due if available)",
                "Enable email/SMS alerts for payment confirmation",
            ],
            "proof_pack": ["Screenshot of recurring setup", "Confirmation number / receipt", "Copy of bill showing account number"],
        },
        {
            "provider": "Generic Credit Card Autopay",
            "country": "CA",
            "steps": [
                "Open credit card portal/app",
                "Enable Autopay / Pre-authorized payment",
                "Choose amount (minimum/statement balance/fixed)",
                "Choose date (statement date or due date)",
                "Confirm bank account and save",
            ],
            "proof_pack": ["Autopay enabled screenshot", "Bank account last-4 screenshot", "First payment receipt"],
        },
    ]
    created = 0
    for d in defaults:
        create(**d, notes="Seeded default", meta={"seed": True})
        created += 1
    return {"seeded": created}

def list_items(country: str = "", q: str = "", status: str = "active") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if country:
        items = [x for x in items if x.get("country") == (country or "").strip().upper()]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("provider","").lower()) or qq in (x.get("notes","").lower())]
    items.sort(key=lambda x: x.get("provider",""))
    return items[:1000]

def get_one(guide_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_items():
        if x.get("id") == guide_id:
            return x
    return None
