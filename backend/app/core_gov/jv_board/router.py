from __future__ import annotations
from fastapi import APIRouter
from .service import board
from .outbox_updates import create_updates
from .readonly import readonly

router = APIRouter(prefix="/core/jv_board", tags=["core-jv-board"])

@router.get("")
def get():
    return board()

@router.get("/readonly")
def readonly_view(token: str, api_key: str = ""):
    # optional hard guard
    try:
        from backend.app.core_gov.security_keys.guard import check  # type: ignore
        ok, msg = check(api_key=api_key)
        if not ok:
            return {"ok": False, "error": msg}
    except Exception:
        pass
    return readonly(token=token)

@router.post("/outbox_update")
def outbox_update(to: str = "(paste)", channel: str = "email"):
    return create_updates(to=to, channel=channel)
