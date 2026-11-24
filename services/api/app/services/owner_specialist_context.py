"""Read one persisted specialist receipt for private owner conversation."""
import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, lazyload

from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.prime_specialist_schedule import PrimeSpecialistSchedule
from app.models.specialist_assignment import SpecialistAssignment
from app.pantheon.roles import LENSES, Role


def specialist_context(db: Session, schedule_id: UUID, *, require_digest: bool = False) -> dict:
    schedule = db.get(PrimeSpecialistSchedule, schedule_id)
    if schedule is None or not schedule.last_report_event_id:
        raise HTTPException(404, "No specialist report has been recorded for that schedule")
    event = db.scalar(select(LegacyOrchestrationEvent).where(
        LegacyOrchestrationEvent.event_id == schedule.last_report_event_id,
        LegacyOrchestrationEvent.event_type == "PRIME_SPECIALIST_SHADOW_REPORT",
    ))
    try:
        report = json.loads(event.payload_json) if event else {}
        if report.get("schedule_id") != str(schedule_id) or report.get("report_event_id") != schedule.last_report_event_id:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(409, "Specialist receipt does not match the schedule") from None
    from app.routers.prime_specialist_schedules import shadow_report_digest

    digest = report.get("report_sha256")
    if (require_digest or "operating_reassessment" in report or digest) and digest != shadow_report_digest(event.event_id, report):
        raise HTTPException(409, "Specialist report failed integrity checks")
    recommendation = report.get("recommendation") or {}
    return {
        "evidence_class": "INTERNAL_ADVISORY",
        "report_event_id": event.event_id, "schedule_id": str(schedule_id),
        "scope": report.get("scope"), "status": report.get("status"),
        "observed_at": report.get("observed_at"), "trigger": report.get("trigger"),
        "heimdall_decision": recommendation.get("heimdall_decision"),
        "operating_reassessment": report.get("operating_reassessment"),
        "verified_internal_outcome_ids": [
            entry["outcome_event_id"] for entry in report.get("verified_internal_outcomes", [])
        ],
        "independent_loki_cleared": False, "execution_authorized": False,
    }


def pantheon_report_index(db: Session, role: Role | None, after: UUID | None, limit: int) -> dict:
    from app.loki.models import LokiReview, LokiReviewStatus
    from app.loki.review_service import verdict
    from app.pantheon.monitor import report_matches_assignment, utc_now, verified_report

    query = select(SpecialistAssignment).where(SpecialistAssignment.last_report_event_id.is_not(None))
    if role is not None:
        query = query.where(SpecialistAssignment.role == role)
    if after is not None:
        query = query.where(SpecialistAssignment.id > after)
    assignments = db.scalars(query.order_by(SpecialistAssignment.id).limit(limit + 1)).all()
    now = utc_now()
    results = []
    for assignment in assignments[:limit]:
        reference = {"assignment_id": str(assignment.id), "role": assignment.role}
        try:
            report = verified_report(db, assignment.last_report_event_id)
            if not report_matches_assignment(assignment, report):
                raise ValueError
            review = db.scalar(select(LokiReview).options(lazyload(LokiReview.findings)).filter_by(
                artifact_type="pantheon_report", artifact_sha256=report["report_sha256"],
                heimdall_reference_id=assignment.last_report_event_id,
            ))
            independent = None
            if review is not None:
                independent = {"review_id": str(review.id), "status": review.status}
                if review.status == LokiReviewStatus.COMPLETED:
                    try:
                        challenge = verdict(db, review)
                    except HTTPException:
                        independent["status"] = "integrity_hold"
                    else:
                        independent.update(reconsideration_status=challenge.reconsideration_status,
                                           findings=challenge.key_risks)
            results.append({
                **reference, "state": "VERIFIED_RECEIPT", "report_event_id": report["report_event_id"],
                "report_sha256": report["report_sha256"], "scope": report["scope"],
                "observed_at": report["observed_at"], "report_status": report["status"],
                "lens": LENSES[assignment.role], "trigger": report["trigger"],
                "assignment_state": "expired" if assignment.state == "active" and assignment.expires_at <= now else assignment.state,
                "observation_categories": sorted((report.get("observations") or {}).keys()),
                "independent_loki": independent,
            })
        except (HTTPException, KeyError, TypeError, ValueError, AttributeError):
            results.append({**reference, "state": "INTEGRITY_HOLD"})
    return {"reports": results, "next_after": str(assignments[limit - 1].id) if len(assignments) > limit else None,
            "execution_authorized": False}


def prime_decision_context(db: Session, decision_id: UUID) -> dict:
    from app.loki.models import LokiReview
    from app.loki.review_service import verdict
    from app.models.god_verdicts import GodVerdict

    snapshot = db.get(GodVerdict, decision_id)
    if snapshot is None or snapshot.trigger != "phase3_universal_opportunity":
        raise HTTPException(404, "Prime decision snapshot not found")
    metadata = snapshot.metadata_json
    if not isinstance(metadata, dict) or metadata.get("shadow_mode") is not False:
        raise HTTPException(409, "This snapshot lacks a live reviewed recommendation")
    try:
        linked = metadata["owner_approval_envelope"]["independent_loki"]
        review = db.get(LokiReview, UUID(linked["review_id"]))
        if review is None or review.heimdall_reference_id != metadata.get("opportunity_id"):
            raise ValueError
        independent = verdict(db, review)
        if (independent.artifact_sha256 != linked["artifact_sha256"]
                or independent.result_sha256 != linked.get("result_sha256")
                or independent.reconsideration_sha256 != linked.get("reconsideration_sha256")):
            raise ValueError
    except (KeyError, TypeError, ValueError, AttributeError):
        raise HTTPException(409, "Prime decision and independent evidence do not match") from None

    checked = {}
    proposal = review.raw_input
    inputs = proposal.get("specialist_inputs", {}) if isinstance(proposal, dict) else None
    if not isinstance(inputs, dict):
        raise HTTPException(409, "Reviewed proposal has invalid specialist inputs")
    scope = {"legacy_instance_id": proposal.get("legacy"), "business_id": inputs.get("business_id"),
             "engine_id": proposal.get("engine_id"), "jurisdiction": proposal.get("jurisdiction")}
    if "mimir_outcome_claims" in inputs:
        from app.services.prime_business_execution import verify_mimir_claims

        evidence = verify_mimir_claims(db, scope, inputs["mimir_outcome_claims"])
        if evidence != linked.get("reviewed_mimir_outcomes"):
            raise HTTPException(409, "Mimir evidence differs from the reviewed decision")
        checked["reviewed_mimir_outcomes"] = evidence
    if "pantheon_report_ids" in inputs:
        from app.loki.specialist_review import require_reviewed_reports

        evidence = require_reviewed_reports(db, inputs["pantheon_report_ids"], scope)
        if evidence != linked.get("reviewed_specialist_reports"):
            raise HTTPException(409, "Specialist evidence differs from the reviewed decision")
        checked["reviewed_specialist_reports"] = evidence
    if "consumer_research" in inputs:
        from datetime import datetime, timezone

        from app.services.consumer_evidence import reviewed_summary
        from app.services.foundry_discovery import require_current_candidate

        require_current_candidate(db, proposal, scope, datetime.now(timezone.utc).date(), advisory_only=True)
        expected = reviewed_summary(inputs["consumer_research"])
        if expected != linked.get("reviewed_consumer_research"):
            raise HTTPException(409, "Consumer evidence differs from the reviewed decision")
        checked["reviewed_consumer_research"] = expected

    return {
        **checked,
        "prime_decision_id": str(decision_id),
        "opportunity_id": metadata.get("opportunity_id"),
        "heimdall_decision": (snapshot.heimdall_recommendation or {}).get("decision"),
        "independent_loki": {
            "review_id": str(review.id), "proposal_sha256": independent.artifact_sha256,
            "result_sha256": independent.result_sha256, "reconsideration_sha256": independent.reconsideration_sha256,
            "ok_to_proceed": independent.ok_to_proceed, "reconsideration_status": independent.reconsideration_status,
            "findings": independent.key_risks,
        },
        "evidence_class": "REVIEWED_INTERNAL_RECOMMENDATION",
        "execution_authorized": False,
    }
