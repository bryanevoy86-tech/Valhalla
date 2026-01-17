# services/api/app/services/deploy_check.py

"""
Deployment Check Service for PACK V: Deployment Checklist / Ops Automation
Provides pre-deploy and pre-scale sanity checks for operational readiness.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.services.system_introspection import basic_db_health


# Required environment variables for deployment
REQUIRED_ENV_VARS = [
    "DATABASE_URL",
    # Add your critical environment variables here:
    # "SECRET_KEY",
    # "API_KEY",
    # etc.
]

# Required route prefixes (critical subsystems)
REQUIRED_PREFIXES = [
    "/api/health",
    "/debug/routes",
    "/debug/system",
    "/ui-map",
    "/ops/deploy-check",
]


def check_env_vars() -> Dict[str, bool]:
    """
    Check if all required environment variables are present.
    
    Returns a dict mapping env var names to presence (True/False).
    """
    results: Dict[str, bool] = {}
    for key in REQUIRED_ENV_VARS:
        results[key] = os.getenv(key) is not None
    return results


def check_critical_routes(app: FastAPI) -> Dict[str, Any]:
    """
    Verify that all critical route prefixes are registered.
    
    Returns info about missing routes (if any).
    """
    # Get all registered paths
    paths = []
    for route in app.routes:
        if hasattr(route, "path"):
            paths.append(route.path)
    
    # Check for missing required prefixes
    missing: List[str] = []
    for prefix in REQUIRED_PREFIXES:
        if not any(p.startswith(prefix) for p in paths):
            missing.append(prefix)
    
    return {
        "total_routes": len(app.routes),
        "required_prefixes": REQUIRED_PREFIXES,
        "missing_prefixes": missing,
        "ok": len(missing) == 0,
    }


def deploy_check(app: FastAPI, db: Session) -> Dict[str, Any]:
    """
    Run comprehensive deployment readiness check.
    
    Verifies:
    - Environment variables are set
    - Database is reachable
    - Critical routes are registered
    
    Returns overall status and detailed breakdown.
    """
    # Check environment variables
    env_vars = check_env_vars()
    env_ok = all(env_vars.values())
    
    # Check database health
    db_ok = basic_db_health(db)
    
    # Check critical routes
    routes_status = check_critical_routes(app)
    
    # Overall status: all checks must pass
    overall_ok = env_ok and db_ok and routes_status["ok"]
    
    return {
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "overall_ok": overall_ok,
        "checks": {
            "environment": {
                "ok": env_ok,
                "details": env_vars,
            },
            "database": {
                "ok": db_ok,
                "message": "Database connection healthy" if db_ok else "Database connection failed",
            },
            "routes": routes_status,
        },
    }
