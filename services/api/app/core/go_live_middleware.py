"""Go-Live & Kill-Switch enforcement middleware.

This does NOT redesign the system.
It enforces the Prime Laws by preventing unsafe production execution.

Rules:
- If kill_switch_engaged: block all non-exempt routes.
- If go_live_enabled is False: block execution routes in production when enforcement enabled.
- Always allow: docs/openapi, health, system status, governance endpoints.
"""

from __future__ import annotations

import os
from typing import Callable, Awaitable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.db import SessionLocal
from app.services.go_live import read_state


def _truthy(v: str | None) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "yes", "on"}


class GoLiveMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.enforce = _truthy(os.getenv("GO_LIVE_ENFORCE", "0"))
        self.env = os.getenv("ENV", "").lower() or os.getenv("APP_ENV", "").lower()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable]):
        if not self.enforce:
            return await call_next(request)

        path = request.url.path

        if (
            path.startswith("/docs")
            or path.startswith("/openapi")
            or path.startswith("/redoc")
            or path.startswith("/api/system/status")
            or path.startswith("/api/system/health")
            or path.startswith("/api/governance")
            or path.startswith("/health")
        ):
            return await call_next(request)

        if self.env not in {"prod", "production", "live"}:
            return await call_next(request)

        db = SessionLocal()
        try:
            state = read_state(db)
            if state.kill_switch_engaged:
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "KILL_SWITCH_ENGAGED",
                        "message": "Execution blocked by emergency stop.",
                    },
                )

            if not state.go_live_enabled:
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "GO_LIVE_DISABLED",
                        "message": "System is not enabled for production execution.",
                    },
                )
        finally:
            db.close()

        return await call_next(request)
