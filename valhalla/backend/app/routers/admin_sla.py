import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/admin/sla", tags=["admin-sla"])


@router.get("/current")
def current():
    uptime_pct = 99.95
    return JSONResponse({"uptime_pct": uptime_pct, "ts": int(time.time())})
