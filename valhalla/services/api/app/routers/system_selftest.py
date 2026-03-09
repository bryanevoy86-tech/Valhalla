from __future__ import annotations
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/system", tags=["System"])

REQUIRED_PATHS = [
    "/health",
    "/api/governance/runbook/status",
    "/api/governance/floor/trajectory/month",
]

@router.get("/selftest")
def selftest(request: Request):
    """List all mounted routes. OK if required paths present."""
    paths = sorted({r.path for r in request.app.router.routes})
    missing = [p for p in REQUIRED_PATHS if p not in paths]
    return {"ok": len(missing) == 0, "missing": missing, "route_count": len(paths)}

@router.get("/selftest/hard")
def selftest_hard(request: Request):
    """Return 500 if any required paths missing."""
    paths = sorted({r.path for r in request.app.router.routes})
    missing = [p for p in REQUIRED_PATHS if p not in paths]
    if missing:
        return JSONResponse(status_code=500, content={"missing": missing})
    return {"ok": True}
