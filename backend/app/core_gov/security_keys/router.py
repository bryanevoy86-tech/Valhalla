from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter
from . import store

router = APIRouter(prefix="/core/security/keys", tags=["core-security-keys"])

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@router.post("")
def create(label: str = "default"):
    key = store.new_key()
    rec = {"key": key, "label": label or "default", "created_at": _utcnow_iso()}
    items = store.list_keys()
    items.append(rec)
    store.save_keys(items)
    return rec

@router.get("")
def list_items():
    return {"items": store.list_keys()}
