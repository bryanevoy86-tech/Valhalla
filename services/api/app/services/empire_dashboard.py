"""
PACK AF: Unified Empire Dashboard Service
Read-only aggregation from existing engines.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func


def get_empire_dashboard(db: Session) -> Dict[str, Any]:
    """
    Aggregate snapshot of the entire empire from multiple engines.
    All reads are read-only, no modifications.
    """
    try:
        from app.models.holdings import Holding
    except Exception:
        Holding = None

    try:
        from app.models.wholesale import WholesalePipeline
    except Exception:
        WholesalePipeline = None

    try:
        from app.models.dispo import DispoAssignment
    except Exception:
        DispoAssignment = None

    try:
        from app.models.audit_event import AuditEvent
    except Exception:
        AuditEvent = None

    try:
        from app.models.governance_decision import GovernanceDecision
    except Exception:
        GovernanceDecision = None

    try:
        from app.models.system_metadata import SystemMetadata
    except Exception:
        SystemMetadata = None

    try:
        from app.models.education_engine import Enrollment
    except Exception:
        Enrollment = None

    try:
        from app.models.children import ChildrenHub
    except Exception:
        ChildrenHub = None

    # Holdings
    holdings_count = 0
    holdings_value = 0.0
    if Holding:
        try:
            holdings_q = db.query(Holding).filter(Holding.is_active.is_(True))
            holdings_count = holdings_q.count()
            holdings_value = sum(h.value_estimate or 0 for h in holdings_q)
        except Exception:
            pass

    # Pipelines
    wholesale_total = 0
    wholesale_active = 0
    if WholesalePipeline:
        try:
            wholesale_total = db.query(WholesalePipeline).count()
            wholesale_active = db.query(WholesalePipeline).filter(
                WholesalePipeline.stage.in_(["lead", "offer_made", "under_contract"])
            ).count()
        except Exception:
            pass

    dispo_assignments = 0
    if DispoAssignment:
        try:
            dispo_assignments = db.query(DispoAssignment).count()
        except Exception:
            pass

    # Audit / Governance
    open_audits = 0
    if AuditEvent:
        try:
            open_audits = db.query(AuditEvent).filter(AuditEvent.is_resolved.is_(False)).count()
        except Exception:
            pass

    decisions_total = 0
    if GovernanceDecision:
        try:
            decisions_total = db.query(GovernanceDecision).count()
        except Exception:
            pass

    # System metadata
    backend_complete = False
    version = "0.0.0"
    if SystemMetadata:
        try:
            meta = db.query(SystemMetadata).first()
            if meta:
                backend_complete = bool(meta.backend_complete)
                version = meta.version or "0.0.0"
        except Exception:
            pass

    # Education
    enrollments_total = 0
    if Enrollment:
        try:
            enrollments_total = db.query(Enrollment).count()
        except Exception:
            pass

    # Children hubs
    hubs_total = 0
    if ChildrenHub:
        try:
            hubs_total = db.query(ChildrenHub).count()
        except Exception:
            pass

    return {
        "system": {
            "version": version,
            "backend_complete": backend_complete,
        },
        "holdings": {
            "count": holdings_count,
            "total_estimated_value": holdings_value,
        },
        "pipelines": {
            "wholesale_total": wholesale_total,
            "wholesale_active": wholesale_active,
            "dispo_assignments": dispo_assignments,
        },
        "risk_governance": {
            "open_audit_events": open_audits,
            "governance_decisions": decisions_total,
        },
        "education": {
            "enrollments_total": enrollments_total,
        },
        "children": {
            "hubs_total": hubs_total,
        },
    }
