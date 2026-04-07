from fastapi import APIRouter, Request
from services.api.main import app as base_app
import json

from app.core_flags.flags import all_flags
from app.core_launch.manifest import route_allowed, classify_route, get_active_routers
from app.core_launch.system_check import warm_startup
from app.core_launch.go_button import go_button_eval
from app.core_eia.eia_core import generate_monthly_report, compliance_check
from app.core_eia.eia_packet import build_monthly_packet
from app.core_audit.red_flags import run_red_flags

app = base_app

_original_routes = list(app.router.routes)
_kept_routes = []
_pruned_routes = []

for route in _original_routes:
    if route_allowed(route):
        _kept_routes.append(route)
    else:
        _pruned_routes.append(route)

app.router.routes = _kept_routes

launch_router = APIRouter()

def _status_payload():
    startup = warm_startup()
    compliance = compliance_check({})
    red_flags = run_red_flags({})
    go = go_button_eval(startup, compliance, red_flags)

    return {
        "mode": "launch_core",
        "startup": startup,
        "flags": all_flags(),
        "compliance": compliance,
        "red_flags": red_flags,
        "go_button": go,
    }

@launch_router.get("/api/launch/status", tags=["Launch"])
def launch_status():
    kept = []
    pruned = []
    for r in _kept_routes:
        kept.append({
            "path": getattr(r, "path", ""),
            "name": getattr(r, "name", ""),
            "class": classify_route(r),
        })
    for r in _pruned_routes[:200]:
        pruned.append({
            "path": getattr(r, "path", ""),
            "name": getattr(r, "name", ""),
            "class": classify_route(r),
        })
    return {
        **_status_payload(),
        "active_router_manifest": get_active_routers(),
        "kept_route_count": len(_kept_routes),
        "pruned_route_count": len(_pruned_routes),
        "kept_preview": kept[:200],
        "pruned_preview": pruned,
    }

@launch_router.get("/api/go-button/status", tags=["Launch"])
def go_button_status():
    return _status_payload()

@launch_router.get("/api/eia/status", tags=["EIA"])
def eia_status():
    return {
        "phase": "launch_core",
        "startup": warm_startup(),
        "compliance": compliance_check({}),
        "monthly_report_template": generate_monthly_report(),
        "red_flags": run_red_flags({}),
    }

@launch_router.post("/api/eia/check", tags=["EIA"])
def eia_check(payload: dict):
    return {
        "compliance": compliance_check(payload),
        "red_flags": run_red_flags(payload),
    }

@launch_router.get("/api/eia/monthly-report", tags=["EIA"])
def eia_monthly_report(month: str = None):
    return generate_monthly_report(month)

@launch_router.post("/api/eia/build-packet", tags=["EIA"])
async def eia_build_packet(request: Request):
    try:
        payload = await request.json()
    except:
        payload = {}
    month = payload.get("month")
    if not month:
        from datetime import datetime
        month = datetime.utcnow().strftime("%Y-%m")
    return build_monthly_packet(month, payload)

app.include_router(launch_router)
