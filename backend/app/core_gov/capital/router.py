"""Capital endpoints - track usage against hard caps."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..audit.audit_log import audit
from ..canon.canon import ENGINE_CANON
from .store import load_usage, save_usage
from ..security.rbac import require_scopes, require_active_subscription
from ..security.devkey.deps import require_dev_key
from ..rate_limit.deps import rate_limit

router = APIRouter(prefix="/capital", tags=["Core: Capital"])


class CapitalUpdate(BaseModel):
    """Manual capital usage update."""
    engine: str = Field(..., description="Engine name from Canon")
    used_usd: float = Field(..., ge=0, description="Capital used in USD")


@router.get("/status")
def capital_status():
    """Get capital usage status for all capped engines."""
    usage = load_usage()

    caps = []
    for name, spec in ENGINE_CANON.items():
        if spec.hard_cap_usd is not None:
            used = float(usage.get(name, 0.0))
            cap = float(spec.hard_cap_usd)
            pct = (used / cap) if cap > 0 else 0.0
            caps.append(
                {
                    "engine": name,
                    "class": spec.engine_class,
                    "cap_usd": cap,
                    "used_usd": used,
                    "pct": pct,
                    "over": used > cap,
                }
            )

    return {
        "tracked_usage": usage,
        "capped_engines": caps,
        "note": "Manual tracking only. No money movement is performed by this system.",
    }


@router.post("/set")
def capital_set(
    payload: CapitalUpdate,
    _key=Depends(require_dev_key),
    _sub=Depends(require_active_subscription),
    _owner=require_scopes("owner"),
    _rl=rate_limit("capital_set", max_requests=20, window_seconds=60),
):
    """Set capital usage for an engine (manual override)."""
    usage = load_usage()
    usage[payload.engine] = float(payload.used_usd)
    save_usage(usage)
    audit("CAPITAL_SET", {"engine": payload.engine, "used_usd": payload.used_usd})
    return {"ok": True, "engine": payload.engine, "used_usd": payload.used_usd}

