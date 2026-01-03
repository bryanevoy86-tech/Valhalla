"""Phone-first alerts endpoint - failures, warnings, and audit tail."""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter

from ..cone.service import get_cone_state
from ..canon.canon import ENGINE_CANON
from ..jobs.router import _JOBS
from ..engines.registry import _ENGINE_REGISTRY

router = APIRouter(prefix="/alerts", tags=["Core: Alerts"])

AUDIT_PATH = Path("data") / "audit.log"


@router.get("")
def alerts():
    """
    Phone-first alert dashboard: failures, warnings, and audit trail.
    
    Shows:
    - Failed jobs
    - Missing engine registrations
    - Cone band warnings
    - Last 30 audit log entries
    """
    cone = get_cone_state()

    failed_jobs = [j for j in _JOBS.values() if j.status == "FAILED"]
    running_jobs = [j for j in _JOBS.values() if j.status == "RUNNING"]

    canon_engines = set(ENGINE_CANON.keys())
    registered_engines = set(_ENGINE_REGISTRY.keys())
    missing_registrations = sorted(list(canon_engines - registered_engines))

    # Lightweight "reality" warning flags
    warnings = []
    if cone.band in ("C_STABILIZE", "D_SURVIVAL"):
        warnings.append(f"Cone band is {cone.band} (stabilize/survival mode).")
    if len(failed_jobs) > 0:
        warnings.append(f"{len(failed_jobs)} job(s) failed.")
    if len(missing_registrations) > 0:
        warnings.append(
            f"{len(missing_registrations)} Canon engines not registered "
            f"(ok if intentionally idle)."
        )

    audit_tail = []
    if AUDIT_PATH.exists():
        # Last 30 lines max
        lines = AUDIT_PATH.read_text(encoding="utf-8").splitlines()[-30:]
        audit_tail = lines

    return {
        "cone": cone.model_dump(),
        "jobs": {
            "total": len(_JOBS),
            "failed": len(failed_jobs),
            "running": len(running_jobs),
        },
        "engine_registry": {
            "registered_count": len(registered_engines),
            "missing_registrations": missing_registrations,
        },
        "warnings": warnings,
        "audit_tail": audit_tail,
    }
