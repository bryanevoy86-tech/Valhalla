"""
PACK TV: System Log & Audit Trail Router
Provides endpoints for writing and querying centralized system logs.
All endpoints support correlation IDs for request tracing.
Marked as stable API (STABLE CONTRACT).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.schemas.system_log import SystemLogCreate, SystemLogOut, SystemLogList
from app.services.system_log import write_log, list_logs

router = APIRouter(prefix="/system/logs", tags=["System Logs"])


@router.post("/", response_model=SystemLogOut)
def write_log_endpoint(
    payload: SystemLogCreate,
    db: Session = Depends(get_db),
) -> SystemLogOut:
    """
    Write a log entry to the centralized audit trail.
    
    Accepts log entries with optional correlation_id for distributed tracing,
    user_id for audit trails, and JSON context for structured logging.
    
    **STABLE CONTRACT:** This endpoint will not change in breaking ways.
    
    Args:
        payload: SystemLogCreate with level, category, message, etc.
        db: Database session (injected)
    
    Returns:
        SystemLogOut: The created log entry with timestamp and ID
    """
    return write_log(db, payload)


@router.get("/", response_model=SystemLogList)
def list_logs_endpoint(
    level: Optional[str] = Query(None, description="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    category: Optional[str] = Query(None, description="Filter by category (auth, security, deal, finance, system, etc.)"),
    limit: int = Query(200, ge=1, le=2000, description="Max number of logs to return"),
    db: Session = Depends(get_db),
) -> SystemLogList:
    """
    List system logs with optional filtering.
    
    Returns recent logs, optionally filtered by level and category.
    Always returns results in reverse chronological order (newest first).
    
    **STABLE CONTRACT:** This endpoint will remain backwards compatible.
    
    Args:
        level: Optional log level filter (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        category: Optional category filter
        limit: Number of logs to return (1-2000, default 200)
        db: Database session (injected)
    
    Returns:
        SystemLogList: Total count and list of log entries
    """
    items, total = list_logs(db, level=level, category=category, limit=limit)
    return SystemLogList(total=total, items=items)
