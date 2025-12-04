# services/api/app/routers/admin_healthcheck.py

from __future__ import annotations

import os
import platform
from datetime import datetime
from typing import Any, Dict, List

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.freeze.models import FreezeEvent
from app.routers.admin_dependencies import RECOMMENDED_DEPS, _build_dep_status
from app.routers.admin_heimdall import _get_discord_status, AUTO_PR_STATUS_FILE

router = APIRouter(
    prefix="/admin/health",
    tags=["Admin", "Health"],
)


def _db_ping(db: Session) -> Dict[str, Any]:
    """
    Simple DB connectivity check. Works for Postgres and SQLite.
    """
    try:
        db.execute(sa.text("SELECT 1"))
        return {"ok": True, "message": "DB reachable and responding to SELECT 1."}
    except Exception as exc:
        return {
            "ok": False,
            "message": "DB ping failed.",
            "error": str(exc),
        }


def _freeze_events_status(db: Session) -> Dict[str, Any]:
    """
    Check whether freeze_events table exists and is queryable.
    """
    try:
        total = db.query(FreezeEvent).count()
    except (ProgrammingError, OperationalError) as exc:
        return {
            "available": False,
            "message": (
                "freeze_events table not available or DB not ready. "
                "Ensure Postgres migrations are applied."
            ),
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "available": False,
            "message": "Unexpected error while checking freeze_events table.",
            "error": str(exc),
        }

    return {
        "available": True,
        "total": total,
        "message": "freeze_events table is available.",
    }


def _deps_status() -> Dict[str, Any]:
    """
    Reuse the curated dependency list to see what's missing.
    """
    deps = [_build_dep_status(dep) for dep in RECOMMENDED_DEPS]

    installed = [d for d in deps if d["installed"]]
    missing_required = [d for d in deps if not d["installed"] and not d["optional"]]
    missing_optional = [d for d in deps if not d["installed"] and d["optional"]]

    required_cmd = None
    optional_cmd = None
    if missing_required:
        required_pkgs = " ".join(d["name"] for d in missing_required)
        required_cmd = f"pip install {required_pkgs}"
    if missing_optional:
        optional_pkgs = " ".join(d["name"] for d in missing_optional)
        optional_cmd = f"pip install {optional_pkgs}"

    return {
        "all": deps,
        "installed": installed,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "suggested_commands": {
            "required": required_cmd,
            "optional": optional_cmd,
        },
    }


@router.get(
    "/basic",
    summary="Basic healthcheck",
    description="Simple healthcheck: uptime, Python version, platform.",
)
async def basic_healthcheck() -> Dict[str, Any]:
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }


@router.get(
    "/deep",
    summary="Deep healthcheck",
    description=(
        "Deep healthcheck including DB ping, freeze_events table, dependencies, "
        "and Heimdall alert wiring."
    ),
)
async def deep_healthcheck(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # DB ping
    db_status = _db_ping(db)

    # freeze_events
    freeze_status = _freeze_events_status(db)

    # Dependencies
    deps = _deps_status()

    # Heimdall alerts / auto-PR
    heimdall_alerts = _get_discord_status()
    auto_pr_status_exists = AUTO_PR_STATUS_FILE.exists()

    heimdall_status = {
        "alerts": heimdall_alerts,
        "auto_pr_status_file_exists": auto_pr_status_exists,
        "auto_pr_status_file_path": str(AUTO_PR_STATUS_FILE),
    }

    # Overall ready flag (soft)
    missing_required = deps.get("missing_required", []) or []
    deps_ok = len(missing_required) == 0
    db_ok = db_status.get("ok", False)
    freeze_ok = freeze_status.get("available", False)

    ready = db_ok and freeze_ok and deps_ok

    return {
        "status": "ok" if ready else "degraded",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ready_for_production": ready,
        "checks": {
            "db": db_status,
            "freeze_events": freeze_status,
            "dependencies": deps,
            "heimdall": heimdall_status,
        },
    }
