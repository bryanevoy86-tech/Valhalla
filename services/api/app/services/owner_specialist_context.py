"""Read one persisted specialist receipt for private owner conversation."""
import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.prime_specialist_schedule import PrimeSpecialistSchedule


def specialist_context(db: Session, schedule_id: UUID) -> dict:
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
    if ("operating_reassessment" in report or digest) and digest != shadow_report_digest(event.event_id, report):
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
        if independent.artifact_sha256 != linked["artifact_sha256"]:
            raise ValueError
    except (KeyError, TypeError, ValueError, AttributeError):
        raise HTTPException(409, "Prime decision and independent evidence do not match") from None

    return {
        "prime_decision_id": str(decision_id),
        "opportunity_id": metadata.get("opportunity_id"),
        "heimdall_decision": (snapshot.heimdall_recommendation or {}).get("decision"),
        "independent_loki": {
            "review_id": str(review.id), "proposal_sha256": independent.artifact_sha256,
            "ok_to_proceed": independent.ok_to_proceed, "reconsideration_status": independent.reconsideration_status,
            "findings": independent.key_risks,
        },
        "evidence_class": "REVIEWED_INTERNAL_RECOMMENDATION",
        "execution_authorized": False,
    }
