from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, coalesce

from app.db.session import get_db
from app.models.system_health import SystemHealth
from app.models.shield_event import ShieldEvent
from app.models.trust import Trust
from app.models.legacy import Legacy
from app.models.legal_profile import LegalProfile
from app.models.compliance_signal import ComplianceSignal
from app.schemas.empire_status import (
    EmpireStatusOut,
    EmpireHealthSummary,
    EmpireShieldSummary,
    EmpireTrustSummary,
    EmpireLegacySummary,
    EmpireLegalSummary,
    EmpireComplianceSummary,
)

router = APIRouter()


@router.get("/overview", response_model=EmpireStatusOut)
def get_empire_status(db: Session = Depends(get_db)):
    # Health summaries
    health_rows = db.query(SystemHealth).all()
    health = [
        EmpireHealthSummary(
            service_name=h.service_name,
            status=h.status,
            issue_count=h.issue_count,
            last_heartbeat=h.last_heartbeat,
        )
        for h in health_rows
    ]

    # Shield metrics
    total_shield = db.query(func.count(ShieldEvent.id)).scalar() or 0
    pending_shield = (
        db.query(func.count(ShieldEvent.id))
        .filter(ShieldEvent.resolved == "pending")
        .scalar()
        or 0
    )
    high_shield = (
        db.query(func.count(ShieldEvent.id))
        .filter(ShieldEvent.severity.in_(["high", "critical"]))
        .scalar()
        or 0
    )
    shield = EmpireShieldSummary(
        total_events=total_shield,
        pending_events=pending_shield,
        high_severity_events=high_shield,
    )

    # Trusts
    total_trusts = db.query(func.count(Trust.id)).scalar() or 0
    active_trusts = (
        db.query(func.count(Trust.id))
        .filter(Trust.status == "active")
        .scalar()
        or 0
    )
    total_vault_balance = db.query(coalesce(func.sum(Trust.vault_balance), 0.0)).scalar() or 0.0
    trusts = EmpireTrustSummary(
        total_trusts=total_trusts,
        active_trusts=active_trusts,
        total_vault_balance=float(total_vault_balance),
    )

    # Legacies
    total_legacies = db.query(func.count(Legacy.id)).scalar() or 0
    active_legacies = (
        db.query(func.count(Legacy.id))
        .filter(Legacy.status == "active")
        .scalar()
        or 0
    )
    auto_clone_enabled = (
        db.query(func.count(Legacy.id))
        .filter(Legacy.auto_clone_enabled.is_(True))
        .scalar()
        or 0
    )
    legacies = EmpireLegacySummary(
        total_legacies=total_legacies,
        active_legacies=active_legacies,
        auto_clone_enabled=auto_clone_enabled,
    )

    # Legal Profiles
    total_profiles = db.query(func.count(LegalProfile.id)).scalar() or 0
    active_profiles = (
        db.query(func.count(LegalProfile.id))
        .filter(LegalProfile.active.is_(True))
        .scalar()
        or 0
    )
    high_risk_profiles = (
        db.query(func.count(LegalProfile.id))
        .filter(LegalProfile.risk_level == "high")
        .scalar()
        or 0
    )
    legal = EmpireLegalSummary(
        total_profiles=total_profiles,
        active_profiles=active_profiles,
        high_risk_profiles=high_risk_profiles,
    )

    # Compliance signals
    total_signals = db.query(func.count(ComplianceSignal.id)).scalar() or 0
    warn_signals = (
        db.query(func.count(ComplianceSignal.id))
        .filter(ComplianceSignal.severity == "warn")
        .scalar()
        or 0
    )
    critical_signals = (
        db.query(func.count(ComplianceSignal.id))
        .filter(ComplianceSignal.severity == "critical")
        .scalar()
        or 0
    )
    compliance = EmpireComplianceSummary(
        total_signals=total_signals,
        warnings=warn_signals,
        critical=critical_signals,
    )

    return EmpireStatusOut(
        health=health,
        shield=shield,
        trusts=trusts,
        legacies=legacies,
        legal=legal,
        compliance=compliance,
    )
