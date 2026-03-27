"""
P-AUDIT-1: Audit log API router.

POST /core/audit - Log an event
GET /core/audit - List audit events
"""
from fastapi import APIRouter, Query
from typing import Dict, Any, List
from pydantic import BaseModel
from . import store

router = APIRouter(prefix="/core", tags=["audit"])


class AuditEvent(BaseModel):
    """Audit event request model."""
    event_type: str
    payload: Dict[str, Any]


@router.post("/audit", response_model=Dict[str, Any])
async def log_event(event: AuditEvent) -> Dict[str, Any]:
    """
    Log an audit event.
    
    Args:
        event: Event to log
    
    Returns:
        Logged event with timestamp and ID
    """
    return store.append(event.event_type, event.payload)


@router.get("/audit", response_model=List[Dict[str, Any]])
async def list_audit_events(limit: int = Query(100, ge=1, le=1000)) -> List[Dict[str, Any]]:
    """
    List audit events.
    
    Args:
        limit: Maximum number of events (default 100, max 1000)
    
    Returns:
        List of audit events
    """
    return store.list_events(limit=limit)
