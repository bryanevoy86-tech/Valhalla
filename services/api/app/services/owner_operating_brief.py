"""Read bounded private briefing evidence without dispatching workers."""
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.loki.models import LokiFinding, LokiIndependentReceipt, LokiReconsideration, LokiReview, LokiReviewStatus
from app.loki.review_service import verdict
from app.models.audit_log import AuditLog
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.revenue_ledger import RevenueLedger
from app.pantheon.monitor import REPORT_EVENT, verified_report


def operating_evidence(db: Session) -> dict:
    schema = inspect(db.connection())
    report_items = []
    invalid_reports = []
    market_alerts = []
    economic_alerts = []
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
            economic = report.get("observations", {}).get("economic_reassessment")
            if economic and economic["blockers"]:
                economic_alerts.append({"report_id": event_id, "scope": report["scope"],
                                        "basis": economic["basis"], "blockers": economic["blockers"],
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
    return {"latest_specialist_reports": report_items, "invalid_specialist_report_ids": invalid_reports,
            "loki": loki, "latest_integrity_alerts": alerts, "latest_market_alerts": market_alerts, "latest_economic_alerts": economic_alerts, "financials": financials,
            "verified_cash_balance": None}
