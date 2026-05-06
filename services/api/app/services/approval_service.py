"""
VA Approval Service - handle lead approvals and transitions.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.va_lead import VALead
from app.models.va_approval_queue import VAApprovalQueue
from app.services.va_audit_service import log_va_event


def approve_lead(approval_id: int, approved_by: str, db: Session) -> dict:
    """Approve a VA lead for the next pipeline step."""
    approval = db.query(VAApprovalQueue).filter(VAApprovalQueue.id == approval_id).first()
    if not approval:
        return {"success": False, "error": "Approval not found"}
    
    if approval.status != "pending":
        return {"success": False, "error": f"Approval already {approval.status}"}
    
    # Update approval
    approval.status = "approved"
    approval.approved_by = approved_by
    approval.approved_at = datetime.now(timezone.utc)
    
    # Update lead status
    lead = db.query(VALead).filter(VALead.id == approval.va_lead_id).first()
    if lead:
        lead.status = "approved"
        lead.stage = "approved"
        lead.approved_at = datetime.now(timezone.utc)
        db.add(lead)
    
    db.add(approval)
    db.commit()
    
    # Log the event
    log_va_event(
        actor=approved_by,
        action="approval_approved",
        entity_type="va_approval_queue",
        entity_id=approval_id,
        details=f"Lead {approval.va_lead_id} approved for {approval.recommended_action}",
        db=db
    )
    
    return {
        "success": True,
        "approval_id": approval_id,
        "lead_id": approval.va_lead_id,
        "status": "approved",
        "next_action": approval.recommended_action
    }


def deny_lead(approval_id: int, denied_by: str, denial_reason: str, db: Session) -> dict:
    """Deny a VA lead approval."""
    approval = db.query(VAApprovalQueue).filter(VAApprovalQueue.id == approval_id).first()
    if not approval:
        return {"success": False, "error": "Approval not found"}
    
    if approval.status != "pending":
        return {"success": False, "error": f"Approval already {approval.status}"}
    
    # Update approval
    approval.status = "denied"
    approval.denied_by = denied_by
    approval.denied_at = datetime.now(timezone.utc)
    approval.denial_reason = denial_reason
    
    # Update lead status
    lead = db.query(VALead).filter(VALead.id == approval.va_lead_id).first()
    if lead:
        lead.status = "rejected"
        lead.stage = "rejected"
        db.add(lead)
    
    db.add(approval)
    db.commit()
    
    # Log the event
    log_va_event(
        actor=denied_by,
        action="approval_denied",
        entity_type="va_approval_queue",
        entity_id=approval_id,
        details=f"Lead {approval.va_lead_id} denied. Reason: {denial_reason}",
        db=db
    )
    
    return {
        "success": True,
        "approval_id": approval_id,
        "lead_id": approval.va_lead_id,
        "status": "denied",
        "reason": denial_reason
    }


def get_pending_approvals(db: Session, limit: int = 50) -> list:
    """Get all pending approvals."""
    approvals = db.query(VAApprovalQueue).filter(
        VAApprovalQueue.status == "pending"
    ).order_by(VAApprovalQueue.created_at.desc()).limit(limit).all()
    
    result = []
    for approval in approvals:
        lead = db.query(VALead).filter(VALead.id == approval.va_lead_id).first()
        result.append({
            "approval_id": approval.id,
            "lead_id": approval.va_lead_id,
            "entity_type": approval.entity_type,
            "entity_id": approval.entity_id,
            "recommended_action": approval.recommended_action,
            "heimdall_score": approval.heimdall_score,
            "risk_level": approval.risk_level,
            "assigned_to": approval.assigned_to,
            "created_at": approval.created_at.isoformat() if approval.created_at else None,
            "lead_address": lead.address if lead else None,
            "lead_asking_price": float(lead.asking_price) if lead and lead.asking_price else None,
        })
    
    return result
