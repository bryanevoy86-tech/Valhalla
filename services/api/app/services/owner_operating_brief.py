"""Read bounded private briefing evidence without dispatching workers."""
from datetime import date, datetime, timedelta, timezone
import hashlib
import json

from fastapi import HTTPException
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.loki.evidence import artifact_digest
from app.loki.models import LokiFinding, LokiIndependentReceipt, LokiReconsideration, LokiReview, LokiReviewStatus
from app.loki.review_service import verdict
from app.models.audit_log import AuditLog
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.builder_assignment import BuilderAssignment
from app.models.prime_specialist_schedule import PrimeScheduleTrigger, PrimeSpecialistSchedule
from app.models.specialist_assignment import SpecialistTrigger
from app.models.foundry_intake import FoundryIntakeJob
from app.models.revenue_ledger import RevenueLedger
from app.pantheon.monitor import REPORT_EVENT, verified_report
from app.services.owner_specialist_context import specialist_context


def operating_evidence(db: Session) -> dict:
    schema = inspect(db.connection())
    report_items = []
    invalid_reports = []
    cadence_alerts = []
    market_alerts = []
    economic_alerts = []
    reviewed_economic_scopes = set()
    if schema.has_table(LegacyOrchestrationEvent.__tablename__):
        ids = db.scalars(select(LegacyOrchestrationEvent.event_id).filter_by(
            event_type=REPORT_EVENT,
        ).order_by(LegacyOrchestrationEvent.created_at.desc(), LegacyOrchestrationEvent.id.desc()).limit(10)).all()
        for event_id in ids:
            try:
                report = verified_report(db, event_id)
            except HTTPException:
                invalid_reports.append(event_id)
                continue
            cadence = report.get("cadence")
            if cadence and cadence["missed_slots"]:
                cadence_alerts.append({"report_id": event_id, "role": report["role"], "scope": report["scope"],
                                       "observed_at": report["observed_at"], **cadence})
            economic = report.get("observations", {}).get("economic_reassessment")
            scope_key = tuple(sorted(report["scope"].items())) if economic else None
            if economic and scope_key not in reviewed_economic_scopes:
                reviewed_economic_scopes.add(scope_key)
                if economic["blockers"]:
                    economic_alerts.append({"report_id": event_id, "scope": report["scope"],
                                            "basis": economic["basis"], "blockers": economic["blockers"],
                                            "observed_at": report["observed_at"],
                                            "suggested_action": economic["suggested_action"]})
            market = report.get("observations", {}).get("market_intelligence")
            if market and market["alerts"]:
                market_alerts.append({"report_id": event_id, "observed_at": report["observed_at"],
                                      "scope": report["scope"], "alerts": market["alerts"],
                                      "basis": "SCOPED_SPECIALIST_RESEARCH"})
            report_items.append({key: report[key] for key in (
                "report_event_id", "report_sha256", "role", "scope", "status", "observed_at",
            )})

    prime_alerts, invalid_prime_reports = [], []
    if all(schema.has_table(model.__tablename__) for model in (PrimeSpecialistSchedule, LegacyOrchestrationEvent)):
        schedule = PrimeSpecialistSchedule
        event = LegacyOrchestrationEvent
        latest = db.execute(select(schedule.id, schedule.last_report_event_id).outerjoin(
            event, event.event_id == schedule.last_report_event_id,
        ).where(
            schedule.state == "active", schedule.last_report_event_id.is_not(None),
            schedule.expires_at > datetime.now(timezone.utc).replace(tzinfo=None),
        ).order_by(event.created_at.desc().nulls_last(), schedule.id).limit(10))
        for schedule_id, event_id in latest:
            try:
                advisory = specialist_context(db, schedule_id, require_digest=True)
            except HTTPException:
                invalid_prime_reports.append({"schedule_id": str(schedule_id), "report_event_id": event_id})
                continue
            if advisory["status"] == "blocked" or advisory["heimdall_decision"] == "HOLD":
                reassessment = advisory["operating_reassessment"] or {}
                prime_alerts.append({
                    **{key: advisory[key] for key in (
                        "report_event_id", "schedule_id", "scope", "observed_at", "trigger",
                        "status", "heimdall_decision", "evidence_class", "execution_authorized",
                    )},
                    "blockers": reassessment.get("blockers", []),
                })

    loki = {"available": False, "queued_count": None, "latest_outstanding": []}
    if all(schema.has_table(model.__tablename__) for model in (
        LokiReview, LokiFinding, LokiIndependentReceipt, LokiReconsideration,
    )) and "result_sha256" in {column["name"] for column in schema.get_columns(LokiIndependentReceipt.__tablename__)}:
        loki["available"] = True
        loki["queued_count"] = db.scalar(select(func.count()).select_from(LokiReview).where(
            LokiReview.status == LokiReviewStatus.QUEUED,
        ))
        reviews = db.scalars(select(LokiReview).where(
            LokiReview.status == LokiReviewStatus.COMPLETED,
            LokiReview.result_severity.in_(("warn", "critical")),
        ).order_by(LokiReview.updated_at.desc(), LokiReview.id.desc()).limit(20)).all()
        for review in reviews:
            try:
                decision = verdict(db, review)
            except HTTPException:
                loki["latest_outstanding"].append({"review_id": str(review.id), "status": "INTEGRITY_UNVERIFIED"})
                continue
            if not decision.ok_to_proceed:
                loki["latest_outstanding"].append({
                    "review_id": str(review.id), "artifact_sha256": decision.artifact_sha256,
                    "status": decision.reconsideration_status, "severity": decision.result_severity,
                    "finding_count": len(decision.key_risks),
                })

    alerts = []
    if schema.has_table(AuditLog.__tablename__):
        latest = db.scalars(select(AuditLog).where(AuditLog.event_type == "integrity_alert")
                            .order_by(AuditLog.id.desc()).limit(10)).all()
        alerts = [{"audit_id": item.id, "event_type": item.event_type, "source": item.event_source} for item in latest]

    financials = {"available": False, "basis": "RECORDED_UNRECONCILED_LEDGER", "totals_by_currency": []}
    if schema.has_table(RevenueLedger.__tablename__):
        financials["available"] = True
        since = date.today() - timedelta(days=29)
        totals = db.execute(select(
            RevenueLedger.currency, func.count(), func.sum(RevenueLedger.gross_amount),
        ).where(RevenueLedger.as_of_date.between(since, date.today())).group_by(RevenueLedger.currency)
            .order_by(RevenueLedger.currency)).all()
        financials.update(since=since.isoformat(), totals_by_currency=[
            {"currency": currency, "entries": count, "recorded_gross": str(amount)} for currency, count, amount in totals
        ])
    discovery = {"available": False}
    if schema.has_table(FoundryIntakeJob.__tablename__):
        job = FoundryIntakeJob
        counts = dict(db.execute(select(job.status, func.count()).group_by(job.status)).all())
        latest_errors = db.scalars(select(job).where(job.error_code.is_not(None))
                                 .order_by(job.next_attempt_at.desc(), job.id).limit(5))
        discovery = {"available": True, "counts_by_state": counts,
                     "recent_job_errors": [{"job_id": str(row.id), "status": row.status, "code": row.error_code}
                                           for row in latest_errors],
                     "production_worker_verified": False}
    builder = {"available": False}
    if schema.has_table(BuilderAssignment.__tablename__):
        assignment = BuilderAssignment
        expired = db.scalar(select(func.count()).select_from(assignment).where(
            assignment.status == "leased", assignment.lease_until <= datetime.now(timezone.utc).replace(tzinfo=None),
        ))
        terminal = db.scalar(select(func.count()).select_from(assignment).where(
            assignment.status == "lease_exhausted",
        ))
        builder = {"available": True, "expired_leases": expired, "lease_exhausted": terminal,
                   "release_authorized": False, "production_worker_verified": False}
    research_queue = {}
    for lane, model in (("pantheon", SpecialistTrigger), ("prime", PrimeScheduleTrigger)):
        if schema.has_table(model.__tablename__):
            counts = dict(db.execute(select(model.failure_code, func.count()).group_by(model.failure_code)).all())
            research_queue[lane] = {"queued": counts.pop(None, 0), "failed": sum(counts.values())}
    return {"specialist_queue": research_queue, "latest_specialist_reports": report_items, "invalid_specialist_report_ids": invalid_reports,
            "specialist_cadence_alerts": cadence_alerts, "loki": loki, "latest_integrity_alerts": alerts, "latest_market_alerts": market_alerts, "latest_economic_alerts": economic_alerts, "financials": financials,
            "latest_prime_advisory_alerts": prime_alerts, "invalid_prime_report_refs": invalid_prime_reports,
            "verified_cash_balance": None, "foundry_intake_health": discovery, "builder_lease_health": builder}


def owner_attention(db: Session) -> dict:
    """Project stable owner inbox entries from existing operational receipts."""
    evidence = operating_evidence(db)
    ordered_sources = (
        ("integrity", "audit_id", evidence["latest_integrity_alerts"]),
        ("prime_integrity", "report_event_id", evidence["invalid_prime_report_refs"]),
        ("review", "review_id", evidence["loki"]["latest_outstanding"]),
        ("prime_advisory", "report_event_id", evidence["latest_prime_advisory_alerts"]),
        ("economic", "report_id", evidence["latest_economic_alerts"]),
        ("discovery", "job_id", evidence["foundry_intake_health"].get("recent_job_errors", [])),
        ("schedule", "report_id", evidence["specialist_cadence_alerts"]),
    )
    entries = []
    for category, key, rows in ordered_sources:
        entries.extend({"notification_id": f"{category}:{row[key]}", "category": category, "reference": str(row[key])}
                       for row in rows)
    return {"entries": entries, "view": "PRIVATE_IN_APP", "delivery_attempted": False,
            "execution_authorized": False}

ATTENTION_ACK_TYPE = "OWNER_ATTENTION_ACKNOWLEDGED"


def _attention_ack_identity(owner_id: int, notification_id: str) -> tuple[str, dict]:
    payload = {"owner_id": owner_id, "notification_id": notification_id}
    prepared = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    event_id = "OWNER-ACK-" + hashlib.sha256(prepared).hexdigest()
    return event_id, {**payload, "sha256": artifact_digest(ATTENTION_ACK_TYPE, event_id, payload)}


def _valid_attention_ack(row, payload: dict) -> bool:
    try:
        return (row.event_type == ATTENTION_ACK_TYPE and row.legacy_instance_id is None
                and json.loads(row.payload_json or "null") == payload)
    except (TypeError, ValueError):
        return False


def owner_attention_with_acknowledgments(db: Session, owner_id: int) -> dict:
    result = owner_attention(db)
    expected = dict(_attention_ack_identity(owner_id, entry["notification_id"]) for entry in result["entries"])
    acknowledged = []
    if expected and inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        rows = db.scalars(select(LegacyOrchestrationEvent).where(LegacyOrchestrationEvent.event_id.in_(expected)))
        acknowledged = sorted(expected[row.event_id]["notification_id"] for row in rows
                              if _valid_attention_ack(row, expected[row.event_id]))
    return {**result, "acknowledged_ids": acknowledged}


def acknowledge_owner_attention(db: Session, owner_id: int, notification_id: str) -> dict:
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Owner attention receipts unavailable")
    event_id, payload = _attention_ack_identity(owner_id, notification_id)
    event = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=event_id))
    if event is None:
        if not any(entry["notification_id"] == notification_id for entry in owner_attention(db)["entries"]):
            raise HTTPException(404, "Owner attention item not found")
        db.add(LegacyOrchestrationEvent(
            event_id=event_id, event_type=ATTENTION_ACK_TYPE, message="Owner acknowledged an in-app attention item",
            payload_json=json.dumps(payload),
        ))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        event = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=event_id))
    if event is None or not _valid_attention_ack(event, payload):
        raise HTTPException(409, "Owner attention receipt failed integrity checks")
    return {"notification_id": notification_id, "acknowledged": True, "delivery_attempted": False,
            "execution_authorized": False}
