"""
Metrics router - aggregates counts from all database tables for monitoring.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from ..core.db import get_db

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def get_metrics(db: Session = Depends(get_db)):
    """
    Get aggregate metrics from all tables for monitoring dashboard.
    Returns counts from research, telemetry, capital, builder, and playbook tables.
    """
    metrics = {
        "ok": True,
        "research_sources": 0,
        "research_docs": 0,
        "telemetry_events": 0,
        "capital_intake_records": 0,
        "builder_tasks": 0,
        "playbooks": 0
    }
    
    # Count research sources
    try:
        metrics["research_sources"] = db.execute(
            text("SELECT COUNT(*) FROM research_sources")
        ).scalar() or 0
    except Exception:
        pass
    
    # Count research docs
    try:
        metrics["research_docs"] = db.execute(
            text("SELECT COUNT(*) FROM research_docs")
        ).scalar() or 0
    except Exception:
        pass
    
    # Count telemetry events
    try:
        metrics["telemetry_events"] = db.execute(
            text("SELECT COUNT(*) FROM telemetry_events")
        ).scalar() or 0
    except Exception:
        pass
    
    # Count capital intake records
    try:
        metrics["capital_intake_records"] = db.execute(
            text("SELECT COUNT(*) FROM capital_intake")
        ).scalar() or 0
    except Exception:
        pass
    
    # Count builder tasks
    try:
        metrics["builder_tasks"] = db.execute(
            text("SELECT COUNT(*) FROM builder_tasks")
        ).scalar() or 0
    except Exception:
        pass
    
    # Count playbooks
    try:
        metrics["playbooks"] = db.execute(
            text("SELECT COUNT(*) FROM playbooks")
        ).scalar() or 0
    except Exception:
        pass
    
    return metrics
