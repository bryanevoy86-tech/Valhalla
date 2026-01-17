"""
PACK UJ: Read-Only Shield Middleware
Blocks write requests when maintenance_state.mode is read_only or maintenance.
"""

from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from sqlalchemy.orm import Session
from app.core.db import get_db_session
from app.models.maintenance import MaintenanceState


class ReadOnlyShieldMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        method = request.method.upper()

        # Allow safe methods always
        if method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        # Check maintenance state
        try:
            session_gen = get_db_session()
            db: Session = next(session_gen)
            try:
                state = (
                    db.query(MaintenanceState)
                    .filter(MaintenanceState.id == 1)
                    .first()
                )
            finally:
                db.close()
        except Exception:
            # If DB unavailable, fail open (let error handler handle it)
            state = None

        if state and state.mode in ("read_only", "maintenance"):
            detail = (
                "System is currently in read-only mode." if state.mode == "read_only"
                else "System is in maintenance mode."
            )
            return JSONResponse(
                status_code=503,
                content={
                    "title": "Write operations temporarily disabled",
                    "status": 503,
                    "detail": detail,
                },
            )

        # Otherwise allow
        return await call_next(request)
