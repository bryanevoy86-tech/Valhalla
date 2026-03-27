from app.observability import canary
from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/admin/canary", tags=["admin-canary"])


@router.get("/status")
def get_status():
    return canary.status()


@router.post("/enable")
def enable(flag: bool = Query(True)):
    canary.set_enabled(flag)
    return canary.status()


@router.post("/percent")
def set_percent(p: int = Query(..., ge=0, le=100)):
    canary.set_percent(p)
    return canary.status()


@router.post("/upstream")
def set_upstream(url: str = Query(...)):
    canary.set_upstream(url)
    return canary.status()


@router.post("/clear-failures")
def clear_failures():
    canary.clear_failures()
    return canary.status()


@router.post("/guard")
def guard(x_canary_token: str | None = Header(default=None), severe: bool = Query(False)):
    token = canary.WEBHOOK_TOKEN
    if token and x_canary_token != token:
        raise HTTPException(status_code=401, detail="invalid token")
    st = canary.guard_drop(severe=severe)
    return JSONResponse({"ok": True, "state": st})
