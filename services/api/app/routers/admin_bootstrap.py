# services/api/app/routers/admin_bootstrap.py

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.routers import admin_dashboard
from app.routers.admin_dashboard import (
    _get_dependencies_summary,
    _get_freeze_events_stats,
)
from app.routers.admin_heimdall import _get_discord_status, AUTO_PR_STATUS_FILE

router = APIRouter(
    prefix="/admin/bootstrap",
    tags=["Admin", "Bootstrap"],
)


def _build_step(
    id: str,
    title: str,
    description: str,
    done: bool,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "id": id,
        "title": title,
        "description": description,
        "done": done,
    }
    if details:
        data["details"] = details
    return data


@router.get(
    "/checklist",
    summary="Bootstrap checklist",
    description=(
        "Ordered checklist of steps required to move the system from "
        "degraded → ready, based on current dependencies, DB, and alerts."
    ),
)
async def get_bootstrap_checklist(
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # Route summary from dashboard
    app_routes = [
        route
        for route in request.app.routes
        if hasattr(route, "path") and hasattr(route, "tags")
    ]
    route_summary = admin_dashboard._summarize_routes(  # type: ignore[attr-defined]
        [r for r in app_routes if not admin_dashboard._is_internal_route(r)]  # type: ignore[attr-defined]
    )

    # Dependencies
    deps_summary = _get_dependencies_summary()
    missing_required = deps_summary.get("missing_required", []) or []
    missing_optional = deps_summary.get("missing_optional", []) or []

    # Freeze events / migrations
    freeze_stats = _get_freeze_events_stats(db)
    freeze_available = freeze_stats.get("available", False)

    # Heimdall alerts / auto-PR
    heimdall_alerts = _get_discord_status()
    alerts_configured = bool(heimdall_alerts.get("configured"))
    auto_pr_status_exists = AUTO_PR_STATUS_FILE.exists()

    steps: List[Dict[str, Any]] = []

    # Step 1: Install required dependencies
    steps.append(
        _build_step(
            id="deps_required",
            title="Install required Python dependencies",
            description=(
                "Install all missing REQUIRED deps so all feature routers can load. "
                "Use the pip command shown below."
            ),
            done=len(missing_required) == 0,
            details={
                "missing_required": missing_required,
                "pip_command": deps_summary.get("suggested_commands", {}).get(
                    "required"
                ),
            },
        )
    )

    # Step 2: (Optional) install optional deps
    steps.append(
        _build_step(
            id="deps_optional",
            title="Install optional performance/feature dependencies",
            description=(
                "Install optional deps (reporting, PDF, fuzzy matching) to unlock "
                "full performance and convenience."
            ),
            done=len(missing_optional) == 0,
            details={
                "missing_optional": missing_optional,
                "pip_command": deps_summary.get("suggested_commands", {}).get(
                    "optional"
                ),
            },
        )
    )

    # Step 3: DB migrations / freeze_events table
    steps.append(
        _build_step(
            id="db_migrations",
            title="Run Postgres migrations (including freeze_events)",
            description=(
                "Ensure DATABASE_URL points to Postgres and `alembic upgrade head` "
                "has been run so freeze_events and other tables exist."
            ),
            done=bool(freeze_available),
            details={
                "freeze_events": freeze_stats,
            },
        )
    )

    # Step 4: Configure Heimdall alerts (Discord)
    steps.append(
        _build_step(
            id="alerts",
            title="Configure Heimdall alerts (Discord webhook)",
            description=(
                "Set DISCORD_WEBHOOK_URL so Heimdall can send alerts for critical "
                "errors and freeze events."
            ),
            done=alerts_configured,
            details={
                "alerts_status": heimdall_alerts,
            },
        )
    )

    # Step 5: Auto-PR status file
    steps.append(
        _build_step(
            id="auto_pr",
            title="Run auto-PR at least once",
            description=(
                "Run /admin/heimdall/autopr/run so that the auto-PR status file "
                "is generated and visible in the dashboard."
            ),
            done=auto_pr_status_exists,
            details={
                "auto_pr_status_file_exists": auto_pr_status_exists,
                "auto_pr_status_file_path": str(AUTO_PR_STATUS_FILE),
            },
        )
    )

    # Step 6: Verify system routes & tags
    steps.append(
        _build_step(
            id="routes",
            title="Verify routes and tags",
            description=(
                "Use /debug/routes/summary and /admin/dashboard to verify that "
                "routes are loaded, tagged, and grouped as expected."
            ),
            done=route_summary.get("total_routes", 0) > 0,
            details={
                "routes": route_summary,
            },
        )
    )

    # Global readiness: same rules as dashboard but explained
    readiness = {
        "all_steps_done": all(step["done"] for step in steps),
        "steps_remaining": [s["id"] for s in steps if not s["done"]],
    }

    return {
        "readiness": readiness,
        "steps": steps,
    }
