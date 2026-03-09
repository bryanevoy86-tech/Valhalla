from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from . import store

router = APIRouter(prefix="/core/share_tokens", tags=["core-share-tokens"])

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@router.post("")
def create(scope: str = "jv_board", subject_id: str = "", expires_on: str = ""):
    if (scope or "").strip() == "jv_board" and not (subject_id or "").strip():
        raise HTTPException(status_code=400, detail="subject_id required for jv_board tokens")
    t = store.new_token()
    rec = {"token": t, "scope": (scope or "jv_board").strip(), "subject_id": (subject_id or "").strip(), "expires_on": (expires_on or "").strip(), "status": "active", "created_at": _utcnow_iso()}
    items = store.list_tokens()
    items.append(rec)
    store.save_tokens(items)
    return rec

@router.get("")
def list_items(scope: str = ""):
    items = store.list_tokens()
    if scope:
        items = [x for x in items if x.get("scope") == scope]
    return {"items": items[:2000]}

@router.post("/{token}/revoke")
def revoke(token: str):
    items = store.list_tokens()
    x = next((i for i in items if i.get("token") == token), None)
    if not x:
        raise HTTPException(status_code=404, detail="not found")
    x["status"] = "revoked"; x["revoked_at"] = _utcnow_iso()
    store.save_tokens(items)
    return x
