# services/api/app/routers/debug_runtime.py

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.routing import APIRoute

router = APIRouter(
    prefix="/debug",
    tags=["Debug"],
)


def _is_internal_route(route: APIRoute) -> bool:
    """
    Filter out the FastAPI/OpenAPI internal routes so we only show
    *your* real application routes by default.
    """
    if not isinstance(route, APIRoute):
        return True

    path = route.path or ""
    # FastAPI /docs, /openapi.json, /redoc, etc.
    if path.startswith("/openapi"):
        return True
    if path.startswith("/docs"):
        return True
    if path.startswith("/redoc"):
        return True
    if path.startswith("/metrics"):
        # Prometheus endpoint, already covered via metrics middleware
        return True

    return False


def _route_to_dict(route: APIRoute) -> Dict[str, Any]:
    """
    Convert an APIRoute into a JSON-serializable dict.
    """
    methods = sorted(route.methods or [])
    tags: List[str] = []
    if hasattr(route, "tags") and route.tags:
        tags = list(route.tags)

    # Handler details
    endpoint = route.endpoint
    endpoint_name = getattr(endpoint, "__name__", None) or "unknown"
    endpoint_module = getattr(endpoint, "__module__", None) or "unknown"

    return {
        "path": route.path,
        "name": route.name,
        "methods": methods,
        "tags": tags,
        "endpoint_name": endpoint_name,
        "endpoint_module": endpoint_module,
        "summary": getattr(route, "summary", None),
        "description": getattr(route, "description", None),
        "deprecated": getattr(route, "deprecated", False),
    }


@router.get("/routes/raw", summary="Raw list of all registered routes")
async def get_raw_routes(request: Request) -> Dict[str, Any]:
    """
    Return *all* routes in the app, including FastAPI internals.

    This is mainly useful if you want to see every single route object
    and debug something very low-level.
    """
    raw: List[Dict[str, Any]] = []

    for route in request.app.routes:
        if isinstance(route, APIRoute):
            raw.append(_route_to_dict(route))
        else:
            raw.append(
                {
                    "path": getattr(route, "path", None),
                    "name": getattr(route, "name", None),
                    "type": type(route).__name__,
                }
            )

    return {
        "total": len(raw),
        "routes": raw,
    }


@router.get("/routes", summary="Application routes (filtered)")
async def get_app_routes(request: Request) -> Dict[str, Any]:
    """
    Return only *application* routes:

    - Filters out OpenAPI/docs/redoc/metrics
    - Shows method, path, tags, and originating module
    """
    routes: List[Dict[str, Any]] = []

    for route in request.app.routes:
        if not isinstance(route, APIRoute):
            continue
        if _is_internal_route(route):
            continue

        routes.append(_route_to_dict(route))

    return {
        "total": len(routes),
        "routes": routes,
    }


@router.get("/routes/summary", summary="Route summary by tag and prefix")
async def get_routes_summary(request: Request) -> Dict[str, Any]:
    """
    High-level summary of which areas of the system are active.

    - Groups by tag (FastAPI route tags)
    - Groups by top-level path segment (/api/leads -> group 'api')
    """
    tag_counts: Dict[str, int] = defaultdict(int)
    prefix_counts: Dict[str, int] = defaultdict(int)

    for route in request.app.routes:
        if not isinstance(route, APIRoute):
            continue
        if _is_internal_route(route):
            continue

        # Tags summary
        tags: Optional[List[str]] = getattr(route, "tags", None)
        if tags:
            for tag in tags:
                tag_counts[tag] += 1
        else:
            tag_counts["(untagged)"] += 1

        # Prefix summary: first path segment after leading "/"
        path = route.path or "/"
        path = path.lstrip("/")
        if not path:
            prefix = "/"
        else:
            prefix = "/" + path.split("/")[0]
        prefix_counts[prefix] += 1

    # Convert defaultdicts to normal dicts
    return {
        "by_tag": dict(sorted(tag_counts.items(), key=lambda kv: kv[0])),
        "by_prefix": dict(sorted(prefix_counts.items(), key=lambda kv: kv[0])),
        "total_routes": sum(prefix_counts.values()),
    }
