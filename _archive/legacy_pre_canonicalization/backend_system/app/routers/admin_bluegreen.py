import asyncio
import os
import time

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/admin/bluegreen", tags=["admin-bluegreen"])

EN = os.getenv("BG_ENABLED", "false").lower() in ("1", "true", "yes")
BLUE = os.getenv("BG_BLUE_UPSTREAM", "http://backend:8000").rstrip("/")
GREEN = os.getenv("BG_GREEN_UPSTREAM", "http://backend-green:8000").rstrip("/")
ACTIVE = os.getenv("BG_ACTIVE", "blue")
DRAIN = int(os.getenv("BG_DRAIN_SECONDS", "60"))
WARM_PATH = os.getenv("BG_WARMUP_PATH", "/health")
WARM_OK = os.getenv("BG_WARMUP_OK_SUBSTR", "ok")


def make_status():
    return {"enabled": EN, "active": ACTIVE, "blue": BLUE, "green": GREEN, "drain_s": DRAIN}


@router.get("/status")
def status():
    return make_status()


@router.post("/switch")
async def switch(target: str = Query(..., regex="^(blue|green)$")):
    global ACTIVE
    if not EN:
        return JSONResponse({"ok": False, "error": "disabled"}, status_code=404)
    new_url = BLUE if target == "blue" else GREEN
    try:
        async with httpx.AsyncClient(timeout=5) as cli:
            r = await cli.get(new_url + WARM_PATH)
            if r.status_code // 100 != 2 or WARM_OK not in r.text.lower():
                return {"ok": False, "error": "warmup check failed", "resp": r.text[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    ACTIVE = target
    t0 = time.time()
    while time.time() - t0 < DRAIN:
        await asyncio.sleep(1)
    return {"ok": True, "active": ACTIVE}
