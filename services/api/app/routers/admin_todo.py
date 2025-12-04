# services/api/app/routers/admin_todo.py

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.routers.admin_dashboard import _get_dependencies_summary, _get_freeze_events_stats
from app.routers.admin_heimdall import _get_discord_status, AUTO_PR_STATUS_FILE

router = APIRouter(
    prefix="/admin/todo",
    tags=["Admin", "TODO"],
)


def _task(
    id: str,
    category: str,
    title: str,
    description: str,
    blocking: bool,
    data: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "id": id,
        "category": category,
        "title": title,
        "description": description,
        "blocking": blocking,
    }
    if data:
        payload["data"] = data
    return payload


@router.get(
    "",
    summary="System TODO list",
    description=(
        "Returns a structured TODO list derived from current system status. "
        "Useful for you, other devs, or AI assistants to know what to work on."
    ),
)
async def get_todo_list(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    deps = _get_dependencies_summary()
    missing_required = deps.get("missing_required", []) or []
    missing_optional = deps.get("missing_optional", []) or []

    freeze_stats = _get_freeze_events_stats(db)
    freeze_available = freeze_stats.get("available", False)

    heimdall_alerts = _get_discord_status()
    alerts_configured = bool(heimdall_alerts.get("configured"))
    auto_pr_status_exists = AUTO_PR_STATUS_FILE.exists()

    tasks: List[Dict[str, Any]] = []

    # --- Dependencies tasks ---
    if missing_required:
        tasks.append(
            _task(
                id="deps_install_required",
                category="dependencies",
                title="Install missing REQUIRED dependencies",
                description="Install all missing required packages so all critical routers load.",
                blocking=True,
                data={
                    "missing_required": missing_required,
                    "pip_command": deps.get("suggested_commands", {}).get(
                        "required"
                    ),
                },
            )
        )

    if missing_optional:
        tasks.append(
            _task(
                id="deps_install_optional",
                category="dependencies",
                title="Install missing OPTIONAL dependencies",
                description=(
                    "Install optional packages to unlock extra features "
                    "like PDF reports and fuzzy matching."
                ),
                blocking=False,
                data={
                    "missing_optional": missing_optional,
                    "pip_command": deps.get("suggested_commands", {}).get(
                        "optional"
                    ),
                },
            )
        )

    # --- DB / migrations tasks ---
    if not freeze_available:
        tasks.append(
            _task(
                id="db_apply_migrations",
                category="database",
                title="Apply Postgres migrations (including freeze_events)",
                description=(
                    "Ensure DATABASE_URL points to Postgres and run "
                    "`alembic upgrade head` so all tables are created."
                ),
                blocking=True,
                data={"freeze_events": freeze_stats},
            )
        )

    # --- Heimdall alerts tasks ---
    if not alerts_configured:
        tasks.append(
            _task(
                id="alerts_configure_discord",
                category="alerts",
                title="Configure Discord alerts (Heimdall)",
                description=(
                    "Set DISCORD_WEBHOOK_URL so Heimdall can send alerts "
                    "for critical failures and freeze events."
                ),
                blocking=False,
                data={"alerts_status": heimdall_alerts},
            )
        )

    if not auto_pr_status_exists:
        tasks.append(
            _task(
                id="alerts_run_auto_pr",
                category="alerts",
                title="Run auto-PR job once",
                description=(
                    "Call /admin/heimdall/autopr/run so that the auto-PR status "
                    "file is generated and visible to dashboards."
                ),
                blocking=False,
                data={
                    "auto_pr_status_file_exists": auto_pr_status_exists,
                    "auto_pr_status_file_path": str(AUTO_PR_STATUS_FILE),
                },
            )
        )

    # --- If nothing blocking is left, add guidance for next phase ---
    if not any(t["blocking"] for t in tasks):
        tasks.append(
            _task(
                id="flows_harden_core",
                category="flows",
                title="Harden core business flows",
                description=(
                    "With infra ready, focus on tightening lead → buyer → deal, "
                    "tax tracker + funfund, and King/Queen/Kids flows. "
                    "Add tests and minimal UI screens for each."
                ),
                blocking=False,
            )
        )

    return {
        "tasks": tasks,
        "blocking_tasks": [t for t in tasks if t["blocking"]],
        "non_blocking_tasks": [t for t in tasks if not t["blocking"]],
    }
