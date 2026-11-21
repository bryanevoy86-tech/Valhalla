"""Read bounded private briefing evidence without dispatching workers."""
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.loki.models import LokiFinding, LokiIndependentReceipt, LokiReconsideration, LokiReview, LokiReviewStatus
from app.loki.review_service import verdict
from app.models.audit_log import AuditLog
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.builder_assignment import BuilderAssignment
from app.models.foundry_intake import FoundryIntakeJob
from app.models.revenue_ledger import RevenueLedger
from app.pantheon.monitor import REPORT_EVENT, verified_report


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
    return {"latest_specialist_reports": report_items, "invalid_specialist_report_ids": invalid_reports,
            "specialist_cadence_alerts": cadence_alerts, "loki": loki, "latest_integrity_alerts": alerts, "latest_market_alerts": market_alerts, "latest_economic_alerts": economic_alerts, "financials": financials,
            "verified_cash_balance": None, "foundry_intake_health": discovery, "builder_lease_health": builder}
