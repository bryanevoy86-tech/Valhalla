# services/api/app/services/internal_auditor.py

from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.contract_record import ContractRecord
from app.models.document_route import DocumentRoute
from app.models.pro_task_link import ProfessionalTaskLink
from app.services.deal_finalization import check_deal_ready_for_finalization


def create_audit_event(
    db: Session,
    deal_id: Optional[int],
    professional_id: Optional[int],
    code: str,
    severity: str,
    message: str,
) -> AuditEvent:
    """Create a new audit event."""
    evt = AuditEvent(
        deal_id=deal_id,
        professional_id=professional_id,
        code=code,
        severity=severity,
        message=message,
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


def resolve_audit_event(db: Session, event_id: int) -> Optional[AuditEvent]:
    """Mark an audit event as resolved."""
    evt = db.query(AuditEvent).filter(AuditEvent.id == event_id).first()
    if not evt:
        return None
    evt.is_resolved = True
    evt.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(evt)
    return evt


def scan_deal(db: Session, deal_id: int) -> Dict[str, Any]:
    """
    Run rule-based audit on a deal and emit events where needed.
    
    Checks:
    - Signed contract exists
    - All documents acknowledged
    - All professional tasks complete
    """

    status = check_deal_ready_for_finalization(db, deal_id)
    checklist = status["checklist"]

    events: List[AuditEvent] = []

    # Rule 1: Must have signed contract
    if not checklist["has_signed_contract"]:
        events.append(
            create_audit_event(
                db=db,
                deal_id=deal_id,
                professional_id=None,
                code="MISSING_SIGNED_CONTRACT",
                severity="critical",
                message="Deal has no signed contract.",
            )
        )

    # Rule 2: All documents must be acknowledged
    if not checklist["all_required_docs_acknowledged"]:
        events.append(
            create_audit_event(
                db=db,
                deal_id=deal_id,
                professional_id=None,
                code="DOCS_NOT_ACKNOWLEDGED",
                severity="warning",
                message="Not all routed documents are acknowledged.",
            )
        )

    # Rule 3: All professional tasks must be done
    if not checklist["all_professional_tasks_done"]:
        events.append(
            create_audit_event(
                db=db,
                deal_id=deal_id,
                professional_id=None,
                code="OPEN_PROFESSIONAL_TASKS",
                severity="warning",
                message="One or more professional tasks are still open.",
            )
        )

    return {
        "deal_id": deal_id,
        "issues_found": len(events),
        "checklist": checklist,
        "events": [
            {
                "id": e.id,
                "code": e.code,
                "severity": e.severity,
                "message": e.message,
            }
            for e in events
        ],
    }


def list_open_events(db: Session) -> List[AuditEvent]:
    """Get all unresolved audit events."""
    return db.query(AuditEvent).filter(AuditEvent.is_resolved == False).all()  # noqa: E712


def list_events_for_deal(db: Session, deal_id: int) -> List[AuditEvent]:
    """Get all audit events for a specific deal."""
    return db.query(AuditEvent).filter(AuditEvent.deal_id == deal_id).all()


def get_audit_summary(db: Session) -> Dict[str, Any]:
    """Get summary of audit events by severity."""
    all_events = db.query(AuditEvent).filter(AuditEvent.is_resolved == False).all()  # noqa: E712
    
    return {
        "total_open": len(all_events),
        "critical": len([e for e in all_events if e.severity == "critical"]),
        "warning": len([e for e in all_events if e.severity == "warning"]),
        "info": len([e for e in all_events if e.severity == "info"]),
    }
