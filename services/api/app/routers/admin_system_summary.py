# services/api/app/routers/admin_system_summary.py

from __future__ import annotations

import os
import platform
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Request
from fastapi.routing import APIRoute

from app.routers.admin_heimdall import (
    _get_discord_status,
    AUTO_PR_STATUS_FILE,
)

router = APIRouter(
    prefix="/admin/system",
    tags=["Admin", "System"],
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
    """
    Build summaries by tag and top-level prefix.
    """
    tag_counts: Dict[str, int] = defaultdict(int)
    prefix_counts: Dict[str, int] = defaultdict(int)
    total = 0

    for route in app_routes:
        total += 1

        # Tags
        tags = getattr(route, "tags", None) or []
        if tags:
            for tag in tags:
                tag_counts[tag] += 1
        else:
            tag_counts["(untagged)"] += 1

        # Prefix: first path segment after "/"
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


@router.get(
    "/summary",
    summary="High-level system summary",
    description=(
        "Return a consolidated view of the running system: "
        "route counts, Heimdall alert wiring, and environment hints."
    ),
)
async def get_system_summary(request: Request) -> Dict[str, Any]:
    # ---------- Route summary ----------
    app_routes: List[APIRoute] = []
    for route in request.app.routes:
        if not isinstance(route, APIRoute):
            continue
        if _is_internal_route(route):
            continue
        app_routes.append(route)

    route_summary = _summarize_routes(app_routes)

    # ---------- Heimdall / alerts summary ----------
    heimdall_alerts = _get_discord_status()
    auto_pr_status_exists = AUTO_PR_STATUS_FILE.exists()

    heimdall_summary = {
        "alerts": heimdall_alerts,
        "auto_pr_status_file_exists": auto_pr_status_exists,
        "auto_pr_status_file_path": str(AUTO_PR_STATUS_FILE),
    }

    # ---------- Environment summary ----------
    database_url = os.getenv("DATABASE_URL") or ""
    environment = os.getenv("ENVIRONMENT") or os.getenv("ENV") or ""

    env_summary = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "environment": environment or None,
        "database_url_configured": bool(database_url.strip()),
        "database_url_driver": (
            database_url.split(":", 1)[0] if database_url else None
        ),
        "working_directory": str(Path.cwd()),
    }

    return {
        "routes": route_summary,
        "heimdall": heimdall_summary,
        "environment": env_summary,
    }


@router.get(
    "/env",
    summary="Environment configuration snapshot",
    description="Quick view of selected environment variables (without secrets).",
)
async def get_env_snapshot() -> Dict[str, Any]:
    # Note: do NOT include secrets here.
    database_url = os.getenv("DATABASE_URL") or ""
    environment = os.getenv("ENVIRONMENT") or os.getenv("ENV") or ""
    ngrok_enabled = bool(os.getenv("NGROK_AUTHTOKEN") or "")
    grafana_admin = bool(os.getenv("GF_SECURITY_ADMIN_PASSWORD") or "")

    return {
        "environment": environment or None,
        "database_url_configured": bool(database_url.strip()),
        "database_url_driver": (
            database_url.split(":", 1)[0] if database_url else None
        ),
        "ngrok_configured": ngrok_enabled,
        "grafana_admin_password_set": grafana_admin,
        "vector_enabled": (os.getenv("VECTOR_ENABLED") or "").lower() == "true",
    }
