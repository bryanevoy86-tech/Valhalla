from fastapi import APIRouter, Depends
from security.access import require_level

router = APIRouter()


@router.get("/status", dependencies=[Depends(require_level(1))])
def status():
    # Basic heartbeat; we’ll compute real signals later
    return {"mode": "GREEN", "income_drop_last_30d_pct": 0}


@router.post("/override/black", dependencies=[Depends(require_level(3))])
def force_black():
    # Stub: flip to BLACK (no state persisted yet)
    return {"ok": True, "mode": "BLACK", "msg": "Kill/Shield engaged"}
