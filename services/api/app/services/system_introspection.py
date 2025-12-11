# services/api/app/services/system_introspection.py

"""
System introspection and health checking for PACK S.
Provides route listing, subsystem health, and overall system snapshot.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import FastAPI
from sqlalchemy.orm import Session
from sqlalchemy import text


def list_routes(app: FastAPI) -> List[Dict[str, Any]]:
    """
    Extract all registered routes from the FastAPI application.
    Returns a list of route info dicts with path, name, and methods.
    """
    routes_info: List[Dict[str, Any]] = []
    
    for route in app.routes:
        methods = list(route.methods) if hasattr(route, "methods") else []
        path = getattr(route, "path", None)
        name = getattr(route, "name", None)
        
        routes_info.append(
            {
                "path": path,
                "name": name,
                "methods": sorted(methods),
            }
        )
    
    # Sort by path for easier reading
    routes_info.sort(key=lambda r: r.get("path") or "")
    return routes_info


def basic_db_health(db: Session) -> bool:
    """
    Perform a cheap database health check.
    Just executes a trivial query to confirm connection.
    """
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def check_subsystem_exists(db: Session, table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        db.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
        return True
    except Exception:
        return False


def system_snapshot(app: FastAPI, db: Session) -> Dict[str, Any]:
    """
    Generate a comprehensive system snapshot including route count,
    database health, and subsystem availability.
    """
    
    # Check key subsystems by table existence
    subsystems_health = {
        "professionals": check_subsystem_exists(db, "professionals"),
        "contracts": check_subsystem_exists(db, "contract_records"),
        "documents": check_subsystem_exists(db, "document_routes"),
        "tasks": check_subsystem_exists(db, "pro_task_links"),
        "audit": check_subsystem_exists(db, "audit_events"),
        "governance": check_subsystem_exists(db, "governance_decisions"),
    }
    
    return {
        "routes_count": len(app.routes),
        "db_healthy": basic_db_health(db),
        "subsystems": subsystems_health,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }
