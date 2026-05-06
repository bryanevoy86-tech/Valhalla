"""
VA Audit Service - log all VA intake events for compliance and debugging.
"""

from datetime import datetime, timezone
import json
from sqlalchemy.orm import Session
from app.models.va_audit_log import VAAuditLog


def log_va_event(
    actor: str,
    action: str,
    entity_type: str,
    entity_id: int,
    details: str = None,
    old_value: str = None,
    new_value: str = None,
    status: str = "success",
    db: Session = None
) -> dict:
    """
    Log a VA intake event to the audit trail.
    """
    if not db:
        return {"success": False, "error": "Database session required"}
    
    log_entry = VAAuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        old_value=old_value,
        new_value=new_value,
        status=status,
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(log_entry)
    db.commit()
    
    return {
        "success": True,
        "log_id": log_entry.id,
        "action": action
    }


def get_lead_audit_trail(lead_id: int, db: Session) -> list:
    """
    Get complete audit trail for a VA lead.
    """
    events = db.query(VAAuditLog).filter(
        VAAuditLog.entity_type == "va_lead",
        VAAuditLog.entity_id == lead_id
    ).order_by(VAAuditLog.created_at.asc()).all()
    
    return [
        {
            "id": e.id,
            "actor": e.actor,
            "action": e.action,
            "details": e.details,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None
        }
        for e in events
    ]


def get_approval_audit_trail(approval_id: int, db: Session) -> list:
    """
    Get complete audit trail for an approval.
    """
    events = db.query(VAAuditLog).filter(
        VAAuditLog.entity_type == "va_approval_queue",
        VAAuditLog.entity_id == approval_id
    ).order_by(VAAuditLog.created_at.asc()).all()
    
    return [
        {
            "id": e.id,
            "actor": e.actor,
            "action": e.action,
            "details": e.details,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None
        }
        for e in events
    ]
