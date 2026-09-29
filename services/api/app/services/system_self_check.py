from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core import runtime_flags
from app.models.audit_log import AuditLog
from app.models.completion_registry import (
    DatasetRegistryItem,
    KnowledgeRegistryItem,
    LearningFeedbackRecord,
    LearningTaskQueueItem,
    SourceRegistryItem,
)
from app.models.go_live_state import GoLiveState
from app.models.lead_intake import LeadIntake
from app.models.owner_command import OwnerCommand
from app.models.pending_action import PendingAction
from app.models.va_approval_queue import VAApprovalQueue
from app.services.data_safety import DatasetSafetyInput, evaluate_dataset_safety


OWNER_HEALTH_STATES = {"GREEN", "DEGRADED", "BLOCKED", "CRITICAL"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _component(
    component_id: str,
    name: str,
    scope: str,
    status: str,
    evidence: str,
    impact: str,
    blocking: bool,
    details: dict[str, Any] | None = None,
    owner_action_required: bool = False,
    professional_action_required: bool = False,
    automatic_repair_available: bool = False,
    next_check_seconds: int = 300,
) -> dict[str, Any]:
    normalized = status if status in OWNER_HEALTH_STATES else "DEGRADED"
    return {
        "component_id": component_id,
        "name": name,
        "scope": scope,
        "status": normalized,
        "checked_at": _utc_now().isoformat(),
        "evidence": evidence,
        "impact": impact,
        "owner_action_required": owner_action_required,
        "professional_action_required": professional_action_required,
        "automatic_repair_available": automatic_repair_available,
        "blocking": blocking,
        "details": details or {},
        "next_check": (_utc_now() + timedelta(seconds=next_check_seconds)).isoformat(),
    }


def _overall_status(components: list[dict[str, Any]]) -> str:
    states = {c["status"] for c in components}
    if "CRITICAL" in states:
        return "CRITICAL"
    if "BLOCKED" in states:
        return "BLOCKED"
    if "DEGRADED" in states:
        return "DEGRADED"
    return "GREEN"


def _check_db_health(db: Session) -> dict[str, Any]:
    try:
        db.execute(text("SELECT 1"))
        return _component(
            component_id="database",
            name="Primary Database",
            scope="PROCESS_HEALTH",
            status="GREEN",
            evidence="SELECT 1 successful",
            impact="core persistence path is reachable",
            blocking=False,
        )
    except Exception as exc:
        return _component(
            component_id="database",
            name="Primary Database",
            scope="PROCESS_HEALTH",
            status="CRITICAL",
            evidence=f"database check failed: {exc}",
            impact="API can run but business capabilities are blocked",
            blocking=True,
            owner_action_required=True,
        )


def _check_command_approval_state(db: Session) -> dict[str, Any]:
    try:
        pending_count = db.query(PendingAction).count()
        command_count = db.query(OwnerCommand).count()
        return _component(
            component_id="approval_command",
            name="Approval and Command State",
            scope="BUSINESS_READINESS",
            status="GREEN",
            evidence="pending_actions and owner_commands query succeeded",
            impact="owner approval and command lifecycle is readable",
            blocking=False,
            details={"pending_actions": pending_count, "owner_commands": command_count},
        )
    except OperationalError as exc:
        return _component(
            component_id="approval_command",
            name="Approval and Command State",
            scope="BUSINESS_READINESS",
            status="BLOCKED",
            evidence=f"command/approval tables unavailable: {exc}",
            impact="owner-command lifecycle cannot be validated",
            blocking=True,
            owner_action_required=True,
        )


def _check_worker_lease_state() -> dict[str, Any]:
    heartbeat_file = Path(
        os.getenv("VALHALLA_WORKER_HEARTBEAT_FILE", "heimdall/state/worker_heartbeat.json")
    )
    max_age = int(os.getenv("VALHALLA_WORKER_HEARTBEAT_MAX_AGE_SECONDS", "120"))

    if not heartbeat_file.exists():
        return _component(
            component_id="worker_lease",
            name="Worker and Lease State",
            scope="PROCESS_HEALTH",
            status="DEGRADED",
            evidence="heartbeat file missing",
            impact="worker liveness cannot be proven",
            blocking=False,
            owner_action_required=True,
            details={"heartbeat_file": str(heartbeat_file)},
        )

    try:
        payload = json.loads(heartbeat_file.read_text(encoding="utf-8"))
        ts = float(payload.get("ts", 0))
        age = max(0.0, time.time() - ts)
        if age > max_age:
            return _component(
                component_id="worker_lease",
                name="Worker and Lease State",
                scope="PROCESS_HEALTH",
                status="BLOCKED",
                evidence=f"worker heartbeat stale ({age:.1f}s > {max_age}s)",
                impact="dispatch and queue processing safety is uncertain",
                blocking=True,
                owner_action_required=True,
                details={"heartbeat_age_seconds": age, "max_age_seconds": max_age},
            )
        return _component(
            component_id="worker_lease",
            name="Worker and Lease State",
            scope="PROCESS_HEALTH",
            status="GREEN",
            evidence="heartbeat freshness within threshold",
            impact="worker lease liveness is healthy",
            blocking=False,
            details={"heartbeat_age_seconds": age, "max_age_seconds": max_age},
        )
    except Exception as exc:
        return _component(
            component_id="worker_lease",
            name="Worker and Lease State",
            scope="PROCESS_HEALTH",
            status="DEGRADED",
            evidence=f"failed to parse heartbeat: {exc}",
            impact="worker lease state is unreadable",
            blocking=False,
            owner_action_required=True,
        )


def _check_emergency_stop() -> dict[str, Any]:
    raw = os.getenv("VALHALLA_EMERGENCY_STOP", "0").strip().lower()
    active = raw in {"1", "true", "yes", "on"}
    if active:
        return _component(
            component_id="emergency_stop",
            name="Emergency Stop",
            scope="BUSINESS_READINESS",
            status="CRITICAL",
            evidence="VALHALLA_EMERGENCY_STOP is active",
            impact="live execution must remain blocked",
            blocking=True,
            owner_action_required=True,
        )
    return _component(
        component_id="emergency_stop",
        name="Emergency Stop",
        scope="BUSINESS_READINESS",
        status="GREEN",
        evidence="emergency stop not active",
        impact="no emergency stop block in current runtime",
        blocking=False,
    )


def _check_registry_health(db: Session) -> dict[str, Any]:
    try:
        source_count = db.query(SourceRegistryItem).count()
        knowledge_count = db.query(KnowledgeRegistryItem).count()
        status = "GREEN" if source_count > 0 and knowledge_count > 0 else "DEGRADED"
        return _component(
            component_id="knowledge_source_registry",
            name="Knowledge and Source Registry",
            scope="BUSINESS_READINESS",
            status=status,
            evidence="registry tables queried successfully",
            impact="knowledge/source trust metadata visibility available",
            blocking=False,
            details={"source_count": source_count, "knowledge_count": knowledge_count},
            owner_action_required=status != "GREEN",
        )
    except OperationalError as exc:
        return _component(
            component_id="knowledge_source_registry",
            name="Knowledge and Source Registry",
            scope="BUSINESS_READINESS",
            status="BLOCKED",
            evidence=f"registry tables unavailable: {exc}",
            impact="trust and provenance controls cannot be verified",
            blocking=True,
            owner_action_required=True,
        )


def _check_knowledge_freshness(db: Session) -> dict[str, Any]:
    try:
        today = _utc_now().date()
        stale_threshold = today - timedelta(days=30)
        rows = (
            db.query(KnowledgeRegistryItem)
            .filter(KnowledgeRegistryItem.terminal_state == "ACTIVE_AND_VERIFIED")
            .all()
        )
        if not rows:
            return _component(
                component_id="knowledge_freshness",
                name="Knowledge Freshness",
                scope="BUSINESS_READINESS",
                status="DEGRADED",
                evidence="no active verified knowledge rows",
                impact="fresh knowledge basis is thin",
                blocking=False,
                owner_action_required=True,
            )

        stale = [r.item_id for r in rows if r.review_date is None or r.review_date < stale_threshold]
        if stale:
            return _component(
                component_id="knowledge_freshness",
                name="Knowledge Freshness",
                scope="BUSINESS_READINESS",
                status="BLOCKED",
                evidence="critical knowledge review dates are stale or missing",
                impact="unsafe to treat stale knowledge as launch-ready",
                blocking=True,
                owner_action_required=True,
                professional_action_required=True,
                details={"stale_item_ids": stale, "stale_threshold": stale_threshold.isoformat()},
            )

        return _component(
            component_id="knowledge_freshness",
            name="Knowledge Freshness",
            scope="BUSINESS_READINESS",
            status="GREEN",
            evidence="active verified knowledge has fresh review dates",
            impact="knowledge freshness gate passed",
            blocking=False,
        )
    except OperationalError as exc:
        return _component(
            component_id="knowledge_freshness",
            name="Knowledge Freshness",
            scope="BUSINESS_READINESS",
            status="DEGRADED",
            evidence=f"knowledge freshness check unavailable: {exc}",
            impact="freshness gate not verifiable",
            blocking=False,
            owner_action_required=True,
        )


def _check_practice_live_state() -> dict[str, Any]:
    mode = "live" if runtime_flags.is_live() else "sandbox" if runtime_flags.is_sandbox() else "armed"
    if mode == "sandbox":
        status = "DEGRADED"
        impact = "practice mode active; live business readiness is intentionally gated"
    elif mode == "armed":
        status = "DEGRADED"
        impact = "armed mode active; final live promotion still gated"
    else:
        status = "GREEN"
        impact = "runtime mode is live"

    return _component(
        component_id="practice_live_mode",
        name="Practice and Live Mode",
        scope="BUSINESS_READINESS",
        status=status,
        evidence=f"runtime mode: {mode}",
        impact=impact,
        blocking=False,
        details={"mode": mode},
    )


def _check_provider_config() -> dict[str, Any]:
    smtp_ok = bool(os.getenv("SMTP_HOST") and (os.getenv("SMTP_USER") or os.getenv("SMTP_USERNAME")) and (os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD")))
    twilio_ok = bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") and os.getenv("TWILIO_PHONE_NUMBER"))
    docusign_ok = bool(os.getenv("DOCUSIGN_POWERFORM_URL"))

    if smtp_ok or twilio_ok or docusign_ok:
        return _component(
            component_id="critical_providers",
            name="Critical Provider Configuration",
            scope="BUSINESS_READINESS",
            status="GREEN",
            evidence="at least one critical provider path is configured",
            impact="provider integration baseline exists",
            blocking=False,
            details={"smtp": smtp_ok, "twilio": twilio_ok, "docusign": docusign_ok},
        )

    return _component(
        component_id="critical_providers",
        name="Critical Provider Configuration",
        scope="BUSINESS_READINESS",
        status="BLOCKED",
        evidence="SMTP/Twilio/DocuSign critical config missing",
        impact="communications/document external flows are not launch-ready",
        blocking=True,
        owner_action_required=True,
        details={"smtp": smtp_ok, "twilio": twilio_ok, "docusign": docusign_ok},
    )


def _check_future_engine_locks() -> dict[str, Any]:
    raw = (os.getenv("VALHALLA_FUTURE_ENGINES_ACTIVE") or "").strip()
    active = [v.strip() for v in raw.split(",") if v.strip()]
    if active:
        return _component(
            component_id="future_engine_locks",
            name="Future Engine Locks",
            scope="BUSINESS_READINESS",
            status="BLOCKED",
            evidence="future engines are active before launch authorization",
            impact="future-engine safety lock violated",
            blocking=True,
            owner_action_required=True,
            details={"active_future_engines": active},
        )

    return _component(
        component_id="future_engine_locks",
        name="Future Engine Locks",
        scope="BUSINESS_READINESS",
        status="GREEN",
        evidence="no future engines marked active",
        impact="future-engine lock posture is healthy",
        blocking=False,
    )


def _check_queue_health(db: Session) -> dict[str, Any]:
    try:
        pending_actions = db.query(PendingAction).filter(PendingAction.status == "PENDING").count()
        learning_queue = db.query(LearningTaskQueueItem).filter(LearningTaskQueueItem.status == "queued").count()
        owner_active = db.query(OwnerCommand).filter(OwnerCommand.command_state.in_(["APPROVED", "EXECUTING"])).count()

        total_queue_pressure = pending_actions + learning_queue + owner_active
        if total_queue_pressure >= 150:
            status = "BLOCKED"
        elif total_queue_pressure >= 50:
            status = "DEGRADED"
        else:
            status = "GREEN"

        return _component(
            component_id="queue_health",
            name="Queue Health",
            scope="PROCESS_HEALTH",
            status=status,
            evidence="queue pressure calculated from pending actions, learning queue, and owner commands",
            impact="queue throughput and operator responsiveness monitoring",
            blocking=status == "BLOCKED",
            owner_action_required=status != "GREEN",
            details={
                "pending_actions": pending_actions,
                "learning_queued": learning_queue,
                "owner_commands_active": owner_active,
                "queue_pressure": total_queue_pressure,
            },
        )
    except OperationalError as exc:
        return _component(
            component_id="queue_health",
            name="Queue Health",
            scope="PROCESS_HEALTH",
            status="DEGRADED",
            evidence=f"queue health unavailable: {exc}",
            impact="queue pressure is not verifiable",
            blocking=False,
            owner_action_required=True,
        )


def _check_approval_backlog(db: Session) -> dict[str, Any]:
    try:
        pending_actions = db.query(PendingAction).filter(PendingAction.status == "PENDING").count()
        va_pending = db.query(VAApprovalQueue).filter(VAApprovalQueue.status == "pending").count()
        backlog = pending_actions + va_pending

        status = "GREEN"
        if backlog >= 75:
            status = "BLOCKED"
        elif backlog >= 25:
            status = "DEGRADED"

        return _component(
            component_id="approval_backlog",
            name="Approval Backlog",
            scope="BUSINESS_READINESS",
            status=status,
            evidence="approval backlog calculated from pending_actions and va_approval_queue",
            impact="approval latency and command execution readiness",
            blocking=status == "BLOCKED",
            owner_action_required=status != "GREEN",
            details={"pending_actions": pending_actions, "va_pending": va_pending, "backlog": backlog},
        )
    except OperationalError as exc:
        return _component(
            component_id="approval_backlog",
            name="Approval Backlog",
            scope="BUSINESS_READINESS",
            status="DEGRADED",
            evidence=f"approval backlog unavailable: {exc}",
            impact="approval latency cannot be measured",
            blocking=False,
            owner_action_required=True,
        )


def _check_learning_reverify_backlog(db: Session) -> dict[str, Any]:
    try:
        open_reverify = db.query(LearningTaskQueueItem).filter(
            LearningTaskQueueItem.task_type == "REVERIFY_KNOWLEDGE",
            LearningTaskQueueItem.status.in_(["queued", "in_progress", "blocked"]),
        ).count()

        status = "GREEN"
        if open_reverify >= 40:
            status = "BLOCKED"
        elif open_reverify >= 10:
            status = "DEGRADED"

        return _component(
            component_id="learning_reverify_backlog",
            name="Learning Re-Verification Backlog",
            scope="BUSINESS_READINESS",
            status=status,
            evidence="open REVERIFY_KNOWLEDGE tasks measured",
            impact="stale evidence remediation throughput",
            blocking=status == "BLOCKED",
            owner_action_required=status != "GREEN",
            professional_action_required=status == "BLOCKED",
            details={"open_reverify_tasks": open_reverify},
        )
    except OperationalError as exc:
        return _component(
            component_id="learning_reverify_backlog",
            name="Learning Re-Verification Backlog",
            scope="BUSINESS_READINESS",
            status="DEGRADED",
            evidence=f"re-verification backlog unavailable: {exc}",
            impact="stale-evidence remediation not verifiable",
            blocking=False,
            owner_action_required=True,
        )


def _check_stale_task_detection(db: Session) -> dict[str, Any]:
    try:
        stale_cutoff = _utc_now().replace(tzinfo=None) - timedelta(hours=24)
        stale_learning = db.query(LearningTaskQueueItem).filter(
            LearningTaskQueueItem.status.in_(["queued", "in_progress", "blocked"]),
            LearningTaskQueueItem.created_at < stale_cutoff,
        ).count()
        stale_commands = db.query(OwnerCommand).filter(
            OwnerCommand.command_state.in_(["APPROVED", "EXECUTING"]),
            OwnerCommand.created_at < stale_cutoff,
        ).count()

        stale_total = stale_learning + stale_commands
        status = "GREEN" if stale_total == 0 else "DEGRADED" if stale_total < 20 else "BLOCKED"

        return _component(
            component_id="stale_task_detection",
            name="Stale Task Detection",
            scope="PROCESS_HEALTH",
            status=status,
            evidence="stale open tasks and commands measured (>24h)",
            impact="aging work can cause silent degradation",
            blocking=status == "BLOCKED",
            owner_action_required=status != "GREEN",
            details={
                "stale_learning_tasks": stale_learning,
                "stale_owner_commands": stale_commands,
                "stale_total": stale_total,
            },
        )
    except OperationalError as exc:
        return _component(
            component_id="stale_task_detection",
            name="Stale Task Detection",
            scope="PROCESS_HEALTH",
            status="DEGRADED",
            evidence=f"stale task detection unavailable: {exc}",
            impact="stale work cannot be assessed",
            blocking=False,
            owner_action_required=True,
        )


def _check_lead_flow_degradation(db: Session) -> dict[str, Any]:
    try:
        stale_cutoff = _utc_now().replace(tzinfo=None) - timedelta(hours=12)
        stuck_leads = db.query(LeadIntake).filter(LeadIntake.status == "new", LeadIntake.created_at < stale_cutoff).count()
        status = "GREEN" if stuck_leads == 0 else "DEGRADED" if stuck_leads < 20 else "BLOCKED"
        return _component(
            component_id="lead_flow_degradation",
            name="Lead Flow Degradation",
            scope="BUSINESS_READINESS",
            status=status,
            evidence="lead intake rows in 'new' state older than 12h measured",
            impact="lead processing throughput may be degraded",
            blocking=status == "BLOCKED",
            owner_action_required=status != "GREEN",
            details={"stuck_new_leads": stuck_leads},
        )
    except OperationalError as exc:
        return _component(
            component_id="lead_flow_degradation",
            name="Lead Flow Degradation",
            scope="BUSINESS_READINESS",
            status="DEGRADED",
            evidence=f"lead flow degradation unavailable: {exc}",
            impact="lead processing health unknown",
            blocking=False,
            owner_action_required=True,
        )


def _check_va_operator_degradation(db: Session) -> dict[str, Any]:
    try:
        stale_cutoff = _utc_now().replace(tzinfo=None) - timedelta(hours=8)
        stale_va = db.query(VAApprovalQueue).filter(
            VAApprovalQueue.status == "pending",
            VAApprovalQueue.created_at < stale_cutoff,
        ).count()
        status = "GREEN" if stale_va == 0 else "DEGRADED" if stale_va < 15 else "BLOCKED"
        return _component(
            component_id="va_operator_degradation",
            name="VA/Operator Degradation",
            scope="BUSINESS_READINESS",
            status=status,
            evidence="pending VA approvals older than 8h measured",
            impact="VA/operator handoff latency may block workflows",
            blocking=status == "BLOCKED",
            owner_action_required=status != "GREEN",
            details={"stale_va_pending": stale_va},
        )
    except OperationalError as exc:
        return _component(
            component_id="va_operator_degradation",
            name="VA/Operator Degradation",
            scope="BUSINESS_READINESS",
            status="DEGRADED",
            evidence=f"va/operator degradation unavailable: {exc}",
            impact="VA/operator queue health unknown",
            blocking=False,
            owner_action_required=True,
        )


def _check_credential_expiry_warning() -> dict[str, Any]:
    raw = (os.getenv("VALHALLA_CREDENTIAL_EXPIRY_DATE") or "").strip()
    if not raw:
        return _component(
            component_id="credential_expiry",
            name="Credential Expiry Warning",
            scope="BUSINESS_READINESS",
            status="DEGRADED",
            evidence="VALHALLA_CREDENTIAL_EXPIRY_DATE not configured",
            impact="credential rollover horizon is unknown",
            blocking=False,
            owner_action_required=True,
        )
    try:
        expiry = datetime.fromisoformat(raw).date()
    except ValueError:
        return _component(
            component_id="credential_expiry",
            name="Credential Expiry Warning",
            scope="BUSINESS_READINESS",
            status="DEGRADED",
            evidence="credential expiry date format is invalid",
            impact="credential rollover horizon cannot be computed",
            blocking=False,
            owner_action_required=True,
            details={"provided_value": raw},
        )

    days_remaining = (expiry - _utc_now().date()).days
    if days_remaining < 0:
        status = "BLOCKED"
    elif days_remaining <= 14:
        status = "DEGRADED"
    else:
        status = "GREEN"

    return _component(
        component_id="credential_expiry",
        name="Credential Expiry Warning",
        scope="BUSINESS_READINESS",
        status=status,
        evidence="credential expiry horizon computed",
        impact="credential continuity monitoring",
        blocking=status == "BLOCKED",
        owner_action_required=status != "GREEN",
        details={"days_remaining": days_remaining, "expiry_date": expiry.isoformat()},
    )


def _check_evidence_ethics_alerts(db: Session) -> dict[str, Any]:
    try:
        hard_stale = db.query(KnowledgeRegistryItem).filter(KnowledgeRegistryItem.review_date < (_utc_now().date() - timedelta(days=730))).count()
        human_review_feedback = db.query(LearningFeedbackRecord).filter(LearningFeedbackRecord.human_review_required.is_(True)).count()
        alerts = hard_stale + human_review_feedback
        status = "GREEN" if alerts == 0 else "DEGRADED" if alerts < 10 else "BLOCKED"
        return _component(
            component_id="evidence_ethics_alerts",
            name="Evidence/Ethics Alerts",
            scope="BUSINESS_READINESS",
            status=status,
            evidence="hard-stale knowledge and human-review-required feedback measured",
            impact="evidence quality and ethics risk posture",
            blocking=status == "BLOCKED",
            owner_action_required=alerts > 0,
            professional_action_required=hard_stale > 0,
            details={"hard_stale_items": hard_stale, "human_review_feedback": human_review_feedback},
        )
    except OperationalError as exc:
        return _component(
            component_id="evidence_ethics_alerts",
            name="Evidence/Ethics Alerts",
            scope="BUSINESS_READINESS",
            status="DEGRADED",
            evidence=f"evidence/ethics alerts unavailable: {exc}",
            impact="ethics risk alerts are unavailable",
            blocking=False,
            owner_action_required=True,
        )


def _check_compliance_alerts(db: Session) -> dict[str, Any]:
    try:
        high_impact_pending = db.query(LearningFeedbackRecord).filter(
            LearningFeedbackRecord.high_impact.is_(True),
            LearningFeedbackRecord.human_review_required.is_(True),
        ).count()
        status = "GREEN" if high_impact_pending == 0 else "DEGRADED" if high_impact_pending < 5 else "BLOCKED"
        return _component(
            component_id="compliance_alerts",
            name="Compliance Alerts",
            scope="BUSINESS_READINESS",
            status=status,
            evidence="high-impact learning items requiring human review measured",
            impact="compliance-sensitive queue monitoring",
            blocking=status == "BLOCKED",
            owner_action_required=high_impact_pending > 0,
            professional_action_required=high_impact_pending > 0,
            details={"high_impact_human_review_required": high_impact_pending},
        )
    except OperationalError as exc:
        return _component(
            component_id="compliance_alerts",
            name="Compliance Alerts",
            scope="BUSINESS_READINESS",
            status="DEGRADED",
            evidence=f"compliance alerts unavailable: {exc}",
            impact="compliance-sensitive monitoring unavailable",
            blocking=False,
            owner_action_required=True,
        )


def _check_shield_pause_kill_controls(db: Session) -> dict[str, Any]:
    shield_mode = (os.getenv("VALHALLA_SHIELD_MODE") or "off").strip().lower() in {"1", "true", "on", "yes"}
    pause_control = (os.getenv("VALHALLA_PAUSE_CONTROL") or "off").strip().lower() in {"1", "true", "on", "yes"}
    try:
        go_live_state = db.query(GoLiveState).filter(GoLiveState.id == 1).first()
    except OperationalError:
        go_live_state = None
    kill_switch = bool(getattr(go_live_state, "kill_switch_engaged", False))
    go_live_enabled = bool(getattr(go_live_state, "go_live_enabled", False))

    fail_safe_active = kill_switch or shield_mode or pause_control

    if kill_switch:
        status = "CRITICAL"
    elif shield_mode or pause_control:
        status = "DEGRADED"
    else:
        status = "GREEN"

    return _component(
        component_id="shield_pause_kill",
        name="Shield/Pause/Kill Controls",
        scope="BUSINESS_READINESS",
        status=status,
        evidence="control-plane flags evaluated",
        impact="fail-safe controls and launch safety posture",
        blocking=kill_switch,
        owner_action_required=kill_switch,
        details={
            "shield_mode": shield_mode,
            "pause_control": pause_control,
            "kill_switch": kill_switch,
            "go_live_enabled": go_live_enabled,
            "fail_safe_active": fail_safe_active,
        },
    )


def _check_liquidity_and_drift_signals() -> dict[str, Any]:
    cash_horizon_days_raw = (os.getenv("VALHALLA_CASH_HORIZON_DAYS") or "").strip()
    drift_pct_raw = (os.getenv("VALHALLA_PROJECTION_DRIFT_PCT") or "").strip()

    try:
        cash_horizon_days = float(cash_horizon_days_raw) if cash_horizon_days_raw else None
    except ValueError:
        cash_horizon_days = None
    try:
        drift_pct = float(drift_pct_raw) if drift_pct_raw else None
    except ValueError:
        drift_pct = None

    if cash_horizon_days is None and drift_pct is None:
        return _component(
            component_id="liquidity_drift_signals",
            name="Liquidity and Drift Signals",
            scope="BUSINESS_READINESS",
            status="DEGRADED",
            evidence="cash horizon and drift signals are not configured",
            impact="financial warning posture is partially blind",
            blocking=False,
            owner_action_required=True,
        )

    warning = False
    blocking = False
    reasons: list[str] = []

    if cash_horizon_days is not None and cash_horizon_days < 30:
        warning = True
        reasons.append("cash horizon below 30 days")
    if cash_horizon_days is not None and cash_horizon_days < 14:
        blocking = True
        reasons.append("cash horizon below 14 days")
    if drift_pct is not None and drift_pct > 20:
        warning = True
        reasons.append("projection drift above 20%")
    if drift_pct is not None and drift_pct > 35:
        blocking = True
        reasons.append("projection drift above 35%")

    status = "BLOCKED" if blocking else "DEGRADED" if warning else "GREEN"
    return _component(
        component_id="liquidity_drift_signals",
        name="Liquidity and Drift Signals",
        scope="BUSINESS_READINESS",
        status=status,
        evidence="cash horizon and drift metrics evaluated",
        impact="capital runway and forecast integrity warnings",
        blocking=blocking,
        owner_action_required=warning or blocking,
        details={
            "cash_horizon_days": cash_horizon_days,
            "projection_drift_pct": drift_pct,
            "reasons": reasons,
        },
    )


def _check_provider_failure_state() -> dict[str, Any]:
    raw = (os.getenv("VALHALLA_PROVIDER_FAILURE_STATE") or "").strip().lower()
    failures = [v.strip() for v in raw.split(",") if v.strip()]

    if not failures:
        return _component(
            component_id="provider_failure_state",
            name="Provider/Integration Failure State",
            scope="BUSINESS_READINESS",
            status="GREEN",
            evidence="no provider failures declared",
            impact="external integration baseline stable",
            blocking=False,
        )

    critical_failures = {"banking", "payments", "docusign", "smtp", "twilio"}
    has_critical = any(f in critical_failures for f in failures)
    status = "BLOCKED" if has_critical else "DEGRADED"
    return _component(
        component_id="provider_failure_state",
        name="Provider/Integration Failure State",
        scope="BUSINESS_READINESS",
        status=status,
        evidence="provider failure flags declared in runtime",
        impact="external integration reliability degraded",
        blocking=has_critical,
        owner_action_required=True,
        details={"provider_failures": failures},
    )


def _emit_integrity_alert_audit(db: Session, components: list[dict[str, Any]]) -> int:
    raised = 0
    for comp in components:
        if comp.get("status") not in {"BLOCKED", "CRITICAL"}:
            continue
        try:
            entry = AuditLog(
                deal_id=None,
                event_type="integrity_alert",
                event_source="system",
                message=f"{comp.get('component_id')}::{comp.get('status')}::{comp.get('evidence')}",
                event_data=json.dumps(
                    {
                        "component_id": comp.get("component_id"),
                        "scope": comp.get("scope"),
                        "status": comp.get("status"),
                        "blocking": comp.get("blocking"),
                        "fail_safe_required": comp.get("status") == "CRITICAL" or comp.get("blocking") is True,
                    }
                ),
            )
            db.add(entry)
            raised += 1
        except Exception:
            continue

    if raised > 0:
        try:
            db.commit()
        except Exception:
            db.rollback()
            return 0
    return raised


def _derive_weweb_state(config: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    states: list[str] = []

    servers = config.get("servers") if isinstance(config, dict) else None
    server = servers.get("weweb-ai") if isinstance(servers, dict) else None
    configured = isinstance(server, dict)

    if not configured:
        return {
            "state": "MCP_NOT_CONFIGURED",
            "states": ["MCP_NOT_CONFIGURED"],
            "configured": False,
            "auth_proven": False,
        }

    states.append("MCP_CONFIGURED")

    enabled = bool(server.get("enabled", True))
    transport_ok = server.get("type") == "http"
    url_ok = server.get("url") == "https://ai-api.weweb.io/v1/mcp"

    auth_proven = bool(evidence.get("authenticated"))
    if not auth_proven:
        states.append("AUTH_REQUIRED")
        return {
            "state": "AUTH_REQUIRED",
            "states": states,
            "configured": True,
            "enabled": enabled,
            "transport_ok": transport_ok,
            "url_ok": url_ok,
            "auth_proven": False,
        }

    states.append("AUTHENTICATED")
    if evidence.get("project_discovered"):
        states.append("PROJECT_DISCOVERED")
    if evidence.get("valhalla_project_confirmed"):
        states.append("VALHALLA_PROJECT_CONFIRMED")
    if evidence.get("read_access_proven"):
        states.append("READ_ACCESS_PROVEN")
    if evidence.get("write_capability_available_not_authorized"):
        states.append("WRITE_CAPABILITY_AVAILABLE_NOT_AUTHORIZED")
    if evidence.get("runtime_acceptance_ready"):
        states.append("RUNTIME_ACCEPTANCE_READY")
    if evidence.get("proven"):
        states.append("PROVEN")

    return {
        "state": states[-1],
        "states": states,
        "configured": True,
        "enabled": enabled,
        "transport_ok": transport_ok,
        "url_ok": url_ok,
        "auth_proven": True,
    }


def _check_weweb_connection() -> dict[str, Any]:
    config_path = Path(
        os.getenv("VALHALLA_WEWEB_MCP_CONFIG_PATH", "C:/Users/Lanna/AppData/Roaming/Code/User/mcp.json")
    )
    evidence_path = Path(
        os.getenv("VALHALLA_WEWEB_AUTH_EVIDENCE_PATH", "D:/Valhalla/program/VALHALLA_WEWEB_MCP_TRUTH.json")
    )

    config: dict[str, Any] = {}
    evidence: dict[str, Any] = {}

    config_valid = False
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config_valid = True
        except Exception:
            config_valid = False

    if evidence_path.exists():
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except Exception:
            evidence = {}

    weweb = _derive_weweb_state(config, evidence)
    state = weweb["state"]

    if state in {"MCP_NOT_CONFIGURED", "AUTH_REQUIRED"}:
        return _component(
            component_id="weweb_connection",
            name="WeWeb MCP Runtime Connection",
            scope="BUSINESS_READINESS",
            status="BLOCKED",
            evidence=f"weweb state: {state}",
            impact="WeWeb runtime verification is externally blocked until sign-in completes",
            blocking=True,
            owner_action_required=True,
            details={
                "config_path": str(config_path),
                "evidence_path": str(evidence_path),
                "state_chain": weweb.get("states", []),
                "config_valid": config_valid,
                "transport_ok": weweb.get("transport_ok"),
                "url_ok": weweb.get("url_ok"),
                "enabled": weweb.get("enabled"),
            },
        )

    if state in {"AUTHENTICATED", "PROJECT_DISCOVERED", "VALHALLA_PROJECT_CONFIRMED"}:
        return _component(
            component_id="weweb_connection",
            name="WeWeb MCP Runtime Connection",
            scope="BUSINESS_READINESS",
            status="DEGRADED",
            evidence=f"weweb state: {state}",
            impact="authenticated but read-access proof is incomplete",
            blocking=False,
            details={"state_chain": weweb.get("states", [])},
        )

    return _component(
        component_id="weweb_connection",
        name="WeWeb MCP Runtime Connection",
        scope="BUSINESS_READINESS",
        status="GREEN",
        evidence=f"weweb state: {state}",
        impact="authenticated project read access has been proven",
        blocking=False,
        details={"state_chain": weweb.get("states", [])},
    )


def _check_source_isolation_probe(db: Session, probe_violation: bool) -> dict[str, Any]:
    if not probe_violation:
        return _component(
            component_id="source_isolation",
            name="Source and Dataset Isolation",
            scope="BUSINESS_READINESS",
            status="GREEN",
            evidence="probe skipped by caller",
            impact="isolation policy not actively challenged in this run",
            blocking=False,
        )

    synthetic = db.query(DatasetRegistryItem).filter(DatasetRegistryItem.dataset_type == "SYNTHETIC_OPERATIONAL").first()
    if synthetic is None:
        return _component(
            component_id="source_isolation",
            name="Source and Dataset Isolation",
            scope="BUSINESS_READINESS",
            status="DEGRADED",
            evidence="no synthetic dataset available for violation probe",
            impact="live-block behavior not re-validated in this run",
            blocking=False,
            owner_action_required=True,
        )

    result = evaluate_dataset_safety(
        DatasetSafetyInput(
            dataset_type=synthetic.dataset_type,
            mode="live",
            requested_action="external_execution",
            source_data_class="synthetic",
            learning_eligibility=synthetic.learning_eligibility,
            live_kpi_eligibility=synthetic.live_kpi_eligibility,
            accounting_eligibility=synthetic.accounting_eligibility,
            external_execution_eligibility=synthetic.external_execution_eligibility,
            do_not_contact=synthetic.do_not_contact,
            dataset_jurisdiction=synthetic.jurisdiction,
            request_jurisdiction=synthetic.jurisdiction,
            dataset_business_scope=synthetic.business_engine,
            request_business_scope=synthetic.business_engine,
        )
    )

    if result.allowed:
        return _component(
            component_id="source_isolation",
            name="Source and Dataset Isolation",
            scope="BUSINESS_READINESS",
            status="CRITICAL",
            evidence="synthetic/live violation probe was allowed unexpectedly",
            impact="unsafe data can leak into live execution",
            blocking=True,
            owner_action_required=True,
        )

    return _component(
        component_id="source_isolation",
        name="Source and Dataset Isolation",
        scope="BUSINESS_READINESS",
        status="GREEN",
        evidence=f"violation probe blocked as expected: {result.reason}",
        impact="synthetic data remains isolated from live execution",
        blocking=False,
    )


def run_system_self_check(db: Session, *, probe_isolation_violation: bool = False) -> dict[str, Any]:
    process_components: list[dict[str, Any]] = []
    readiness_components: list[dict[str, Any]] = []

    process_components.append(
        _component(
            component_id="api_process",
            name="API Process Health",
            scope="PROCESS_HEALTH",
            status="GREEN",
            evidence="self-check endpoint executing",
            impact="API process is running",
            blocking=False,
        )
    )
    process_components.append(_check_db_health(db))
    process_components.append(_check_worker_lease_state())
    process_components.append(_check_queue_health(db))
    process_components.append(_check_stale_task_detection(db))

    readiness_components.append(_check_command_approval_state(db))
    readiness_components.append(_check_approval_backlog(db))
    readiness_components.append(_check_learning_reverify_backlog(db))
    readiness_components.append(_check_lead_flow_degradation(db))
    readiness_components.append(_check_va_operator_degradation(db))
    readiness_components.append(_check_credential_expiry_warning())
    readiness_components.append(_check_evidence_ethics_alerts(db))
    readiness_components.append(_check_compliance_alerts(db))
    readiness_components.append(_check_emergency_stop())
    readiness_components.append(_check_shield_pause_kill_controls(db))
    readiness_components.append(_check_liquidity_and_drift_signals())
    readiness_components.append(_check_provider_failure_state())
    readiness_components.append(_check_source_isolation_probe(db, probe_isolation_violation))
    readiness_components.append(_check_registry_health(db))
    readiness_components.append(_check_knowledge_freshness(db))
    readiness_components.append(_check_practice_live_state())
    readiness_components.append(_check_provider_config())
    readiness_components.append(_check_weweb_connection())
    readiness_components.append(_check_future_engine_locks())

    process_status = _overall_status(process_components)
    readiness_status = _overall_status(readiness_components)

    all_components = process_components + readiness_components
    blocked_components = [c for c in all_components if c.get("status") in {"BLOCKED", "CRITICAL"}]
    degraded_components = [c for c in all_components if c.get("status") == "DEGRADED"]
    fail_safe_active = any(
        bool(c.get("details", {}).get("fail_safe_active")) for c in all_components if isinstance(c.get("details"), dict)
    ) or any(c.get("status") == "CRITICAL" for c in all_components)

    alert_events = _emit_integrity_alert_audit(db, all_components)

    readiness_state = "READY" if len(blocked_components) == 0 else "NOT_READY"
    anomaly_state = "ANOMALY_DETECTED" if len(blocked_components) > 0 or len(degraded_components) >= 3 else "NORMAL"

    return {
        "generated_at": _utc_now().isoformat(),
        "process_health": {
            "status": process_status,
            "components": process_components,
        },
        "business_capability_readiness": {
            "status": readiness_status,
            "components": readiness_components,
        },
        "readiness_state": readiness_state,
        "system_blocker_count": len(blocked_components),
        "degraded_component_count": len(degraded_components),
        "anomaly_detection": {
            "state": anomaly_state,
            "blocked_components": [c.get("component_id") for c in blocked_components],
            "degraded_components": [c.get("component_id") for c in degraded_components],
        },
        "fail_safe_state": {
            "active": fail_safe_active,
            "trigger": "critical_or_control_flag" if fail_safe_active else "none",
        },
        "integrity_audit_trail": {
            "event_type": "integrity_alert",
            "events_emitted": alert_events,
        },
        "overall_status": _overall_status(all_components),
    }
