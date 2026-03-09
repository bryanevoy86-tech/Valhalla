"""
Execution Class Middleware.

This enforces go-live in a precise way:
- In production with enforcement enabled:
    - If kill switch: block everything except exempt routes.
    - If go-live disabled: block only PROD_EXEC endpoints.
- It does NOT touch sandbox/test environments.
"""

from __future__ import annotations

import os
from typing import Callable, Awaitable, Dict, List, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.db import SessionLocal

# If you already added the go-live state model/service, import it.
# If not, add that first (from the earlier Go-Live patch).
from app.services.go_live import read_state

from app.core.execution_class import ExecClass, get_exec_class


def _truthy(v: str | None) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "yes", "on"}


def _env() -> str:
    return (os.getenv("ENV", "") or os.getenv("APP_ENV", "") or "").strip().lower()


class ExecutionClassMiddleware(BaseHTTPMiddleware):
    """
    Classifies an endpoint (decorator OR path rules) and applies governance rules.
    """

    def __init__(self, app):
        super().__init__(app)
        self.enforce = _truthy(os.getenv("GO_LIVE_ENFORCE", "0"))
        self.env = _env()

        # Exempt paths always allowed (observability + governance).
        self.exempt_prefixes: List[str] = [
            "/docs", "/openapi", "/redoc",
            "/health",
            "/api/system/health",
            "/api/system/status",
            "/api/governance",            # governance routers
            "/api/admin",                 # admin dashboards/ops
        ]

        # Path-based defaults for execution class (so you do NOT have to tag 500 endpoints today).
        # You can override per-endpoint with @set_exec_class decorator.
        self.path_defaults: Dict[str, str] = {
            # Production execution-ish areas (mutations/actions) — adjust over time as you confirm.
            "/api/deals": ExecClass.PROD_EXEC.value,
            "/api/intake": ExecClass.PROD_EXEC.value,
            "/api/buyers": ExecClass.PROD_EXEC.value,
            "/api/capital": ExecClass.PROD_EXEC.value,
            "/api/alerts": ExecClass.PROD_EXEC.value,
            "/api/notify": ExecClass.PROD_EXEC.value,
            "/api/followups": ExecClass.PROD_EXEC.value,

            # Explicit sandbox runners
            "/api/sandbox": ExecClass.SANDBOX_EXEC.value,
        }

    def _is_exempt(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.exempt_prefixes)

    def _path_default_class(self, path: str) -> str:
        for prefix, cls in self.path_defaults.items():
            if path.startswith(prefix):
                return cls
        return ExecClass.OBSERVE_ONLY.value

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable]):
        if not self.enforce:
            return await call_next(request)

        # Only enforce in production/live
        if self.env not in {"prod", "production", "live"}:
            return await call_next(request)

        path = request.url.path
        if self._is_exempt(path):
            return await call_next(request)

        endpoint = request.scope.get("endpoint")
        exec_class = get_exec_class(endpoint)  # decorator-based
        if exec_class == ExecClass.OBSERVE_ONLY.value:
            # apply path default for untagged endpoints
            exec_class = self._path_default_class(path)

        # Pull live state (authoritative)
        db = SessionLocal()
        try:
            state = read_state(db)

            # Hard stop: kill switch blocks ALL non-exempt traffic
            if state.kill_switch_engaged:
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "KILL_SWITCH_ENGAGED",
                        "message": "Execution blocked by emergency stop.",
                        "exec_class": exec_class,
                        "path": path,
                    },
                )

            # Go-live disabled: block only PROD_EXEC
            if not state.go_live_enabled and exec_class == ExecClass.PROD_EXEC.value:
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "GO_LIVE_DISABLED",
                        "message": "Production execution is disabled. This endpoint is classified as PROD_EXEC.",
                        "exec_class": exec_class,
                        "path": path,
                    },
                )
        finally:
            db.close()

        return await call_next(request)
