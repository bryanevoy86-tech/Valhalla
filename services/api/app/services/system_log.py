"""
PACK TV: System Log & Audit Trail Service
Manages centralized structured logs with correlation ID support.
Marked as stable API (STABLE CONTRACT).
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.system_log import SystemLog
from app.schemas.system_log import SystemLogCreate, SystemLogOut


def write_log(db: Session, payload: SystemLogCreate) -> SystemLogOut:
    """
    Write a log entry to the database.
    
    Creates a new log entry with timestamp, level, category, and optional
    correlation_id for distributed tracing and audit trail.
    
    STABLE CONTRACT: Response format will not change.
    
    Args:
        db: Database session
        payload: SystemLogCreate with message and optional metadata
    
    Returns:
        SystemLogOut: The created log entry with timestamp and ID
    """
    obj = SystemLog(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return SystemLogOut.from_orm(obj)


def list_logs(
    db: Session,
    level: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 200,
) -> Tuple[List[SystemLogOut], int]:
    """
    List logs with optional filtering.
    
    Returns recent logs in reverse chronological order (newest first),
    optionally filtered by level and category.
    
    STABLE CONTRACT: Result format and ordering will not change.
    
    Args:
        db: Database session
        level: Optional log level filter (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        category: Optional category filter
        limit: Maximum number of logs to return (default 200)
    
    Returns:
        Tuple of (items: List[SystemLogOut], total: int)
            - items: List of matching log entries
            - total: Total count of matching entries (for pagination)
    """
    q = db.query(SystemLog)
    if level:
        q = q.filter(SystemLog.level == level)
    if category:
        q = q.filter(SystemLog.category == category)
    
    total = q.count()
    items = (
        q.order_by(desc(SystemLog.timestamp))
        .limit(limit)
        .all()
    )
    return [SystemLogOut.from_orm(item) for item in items], total
