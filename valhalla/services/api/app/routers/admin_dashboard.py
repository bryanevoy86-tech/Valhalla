# services/api/app/routers/admin_dashboard.py

from __future__ import annotations

import platform
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from fastapi.routing import APIRoute
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.freeze.models import FreezeEvent
from app.routers.admin_dependencies import RECOMMENDED_DEPS, _build_dep_status
from app.routers.admin_heimdall import _get_discord_status, AUTO_PR_STATUS_FILE

router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Admin", "Dashboard"],
)


def _is_internal_route(route: APIRoute) -> bool:
    """
    Filter out FastAPI/OpenAPI internal routes so we only show your
    application routes in the summaries.
    """
    if not isinstance(route, APIRoute):
        return True

    path = route.path or ""
    if path.startswith("/openapi"):
        return True
    if path.startswith("/docs"):
        return True
    if path.startswith("/redoc"):
        return True
    if path.startswith("/metrics"):
        return True

    return False


def _summarize_routes(app_routes: List[APIRoute]) -> Dict[str, Any]:
    from collections import defaultdict

    tag_counts = defaultdict(int)
    prefix_counts = defaultdict(int)
    total = 0

    for route in app_routes:
        total += 1

        tags = getattr(route, "tags", None) or []
        if tags:
            for tag in tags:
                tag_counts[tag] += 1
        else:
            tag_counts["(untagged)"] += 1

        # Prefix: first path segment
        path = (route.path or "/").lstrip("/")
        if not path:
            prefix = "/"
        else:
            prefix = "/" + path.split("/")[0]
        prefix_counts[prefix] += 1

    return {
        "total_routes": total,
        "by_tag": dict(sorted(tag_counts.items(), key=lambda kv: kv[0])),
        "by_prefix": dict(sorted(prefix_counts.items(), key=lambda kv: kv[0])),
    }


def _get_dependencies_summary() -> Dict[str, Any]:
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


def _get_freeze_events_stats(db: Session) -> Dict[str, Any]:
    """
    Try to gather basic stats about freeze_events.
    If the table or DB is not ready, return a soft failure.
    """
    try:
        total = db.query(FreezeEvent).count()
        critical = (
            db.query(FreezeEvent)
            .filter(FreezeEvent.severity == "critical")
            .count()
        )
        unresolved = (
            db.query(FreezeEvent)
            .filter(FreezeEvent.resolved_at.is_(None))
            .count()
        )
    except (ProgrammingError, OperationalError) as exc:
        return {
            "available": False,
            "error": (
                "freeze_events table not available or DB not ready. "
                "Ensure Postgres migrations are applied."
            ),
            "debug": str(exc),
        }

    return {
        "available": True,
        "total": total,
        "critical": critical,
        "unresolved": unresolved,
    }


def _compute_system_ready(
    deps_summary: Dict[str, Any],
    freeze_stats: Dict[str, Any],
    heimdall_alerts: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute a simple readiness status based on:
    - no missing required deps
    - freeze_events table available
    - Discord alerts wired (optional but recommended)
    """
    missing_required = deps_summary.get("missing_required", []) or []
    deps_ok = len(missing_required) == 0

    freezes_ok = freeze_stats.get("available", False)

    alerts_configured = bool(heimdall_alerts.get("configured"))

    # Base readiness: deps + freeze table
    ready = deps_ok and freezes_ok

    return {
        "ready_for_production": ready,
        "deps_ok": deps_ok,
        "freeze_events_ok": freezes_ok,
        "alerts_configured": alerts_configured,
        "notes": [
            "Install missing required dependencies." if not deps_ok else "",
            "Run Postgres migrations so freeze_events is available."
            if not freezes_ok
            else "",
            "Configure DISCORD_WEBHOOK_URL for alerts."
            if not alerts_configured
            else "",
        ],
    }


@router.get(
    "",
    summary="Master system dashboard",
    description=(
        "High-level dashboard combining route summary, dependencies, "
        "Heimdall alerts, freeze event stats, and readiness flags."
    ),
)
async def get_admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # Routes
    app_routes: List[APIRoute] = []
    for route in request.app.routes:
        if not isinstance(route, APIRoute):
            continue
        if _is_internal_route(route):
            continue
        app_routes.append(route)
    route_summary = _summarize_routes(app_routes)

    # Dependencies
    deps_summary = _get_dependencies_summary()

    # Heimdall / alerts
    heimdall_alerts = _get_discord_status()
    auto_pr_status_exists = AUTO_PR_STATUS_FILE.exists()

    heimdall_summary = {
        "alerts": heimdall_alerts,
        "auto_pr_status_file_exists": auto_pr_status_exists,
        "auto_pr_status_file_path": str(AUTO_PR_STATUS_FILE),
    }

    # Freeze events stats
    freeze_stats = _get_freeze_events_stats(db)

    # Readiness
    readiness = _compute_system_ready(
        deps_summary=deps_summary,
        freeze_stats=freeze_stats,
        heimdall_alerts=heimdall_alerts,
    )

    # Environment basics
    env_summary = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }

    return {
        "routes": route_summary,
        "dependencies": deps_summary,
        "heimdall": heimdall_summary,
        "freeze_events": freeze_stats,
        "readiness": readiness,
        "environment": env_summary,
    }
