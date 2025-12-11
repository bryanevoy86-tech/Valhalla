"""
PACK TX: System Health & Metrics Service
Provides health status queries for Kubernetes probes and system monitoring.
Marked as stable API (STABLE CONTRACT).
"""

import time
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.base import Base


_start_time: float = time.time()


def get_health_status() -> Dict[str, Any]:
    """
    Get liveness probe status.
    
    Returns current system health indicating whether the application is alive
    and responsive. Always returns quickly without database queries.
    
    STABLE CONTRACT: Response format and keys will not change.
    
    Returns:
        Dict with keys: status, timestamp, message
            - status: "ok" or "degraded"
            - timestamp: ISO8601 datetime
            - message: Human-readable status message
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "message": "Valhalla backend is alive.",
    }


def get_readiness_status(db: Session) -> Dict[str, Any]:
    """
    Get readiness probe status.
    
    Checks if the application is ready to accept traffic. Performs essential
    checks like database connectivity.
    
    STABLE CONTRACT: Response format and keys will not change.
    
    Args:
        db: Database session for connectivity checks
    
    Returns:
        Dict with keys: status, timestamp, db_ok, message
            - status: "ready" or "maintenance"
            - timestamp: ISO8601 datetime
            - db_ok: Boolean indicating DB connectivity
            - message: Human-readable status message
    """
    db_ok: bool = False
    msg: str = "Readiness check passed."
    try:
        # Try a simple query to verify DB connection
        db.execute("SELECT 1")
        db_ok = True
    except Exception as e:
        db_ok = False
        msg = f"Database check failed: {str(e)}"

    status: str = "ready" if db_ok else "maintenance"

    return {
        "status": status,
        "timestamp": datetime.utcnow(),
        "db_ok": db_ok,
        "message": msg,
    }


def get_basic_metrics() -> Dict[str, Any]:
    """
    Get basic application metrics.
    
    Returns simple metrics like uptime suitable for dashboards. Can be extended
    with request rate, memory usage, etc. in future.
    
    STABLE CONTRACT: Uptime calculation will not change; additional fields may be added.
    
    Returns:
        Dict with keys: timestamp, uptime_seconds, request_rate_hint
    """
    now: float = time.time()
    uptime: float = now - _start_time
    return {
        "timestamp": datetime.utcnow(),
        "uptime_seconds": uptime,
        "request_rate_hint": None,  # can be wired to real metrics later
    }
