"""
PACK TR: Security Action Services
Business logic for action request workflow.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.security_actions import SecurityActionRequest


async def create_action_request(
    db: Session,
    requested_by: str,
    action_type: str,
    payload: dict = None
) -> SecurityActionRequest:
    """Create a new action request."""
    request = SecurityActionRequest(
        requested_by=requested_by,
        action_type=action_type,
        payload=payload,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


async def list_action_requests(
    db: Session,
    status: str = None,
    limit: int = 50
):
    """List action requests, optionally filtered by status."""
    query = db.query(SecurityActionRequest)
    
    if status:
        query = query.filter(SecurityActionRequest.status == status)
    
    items = query.order_by(desc(SecurityActionRequest.created_at)).limit(limit).all()
    total = db.query(SecurityActionRequest).count()
    pending = db.query(SecurityActionRequest).filter(
        SecurityActionRequest.status == "pending"
    ).count()
    
    return {
        "total": total,
        "pending": pending,
        "items": items
    }


async def get_action_request(db: Session, request_id: int) -> SecurityActionRequest:
    """Get a specific action request."""
    return db.query(SecurityActionRequest).filter(
        SecurityActionRequest.id == request_id
    ).first()


async def update_action_request(
    db: Session,
    request_id: int,
    status: str = None,
    approved_by: str = None,
    resolution_notes: str = None,
    executed: bool = False
) -> SecurityActionRequest:
    """Update action request status and approval."""
    request = await get_action_request(db, request_id)
    if not request:
        return None
    
    if status:
        request.status = status
    if approved_by:
        request.approved_by = approved_by
    if resolution_notes:
        request.resolution_notes = resolution_notes
    if executed:
        request.executed_at = datetime.utcnow()
    
    request.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(request)
    return request


async def approve_action(
    db: Session,
    request_id: int,
    approved_by: str
) -> SecurityActionRequest:
    """Approve an action request."""
    return await update_action_request(
        db,
        request_id,
        status="approved",
        approved_by=approved_by
    )


async def reject_action(
    db: Session,
    request_id: int,
    approved_by: str,
    reason: str
) -> SecurityActionRequest:
    """Reject an action request."""
    return await update_action_request(
        db,
        request_id,
        status="rejected",
        approved_by=approved_by,
        resolution_notes=reason
    )
