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
    recommendation = report.get("recommendation") or {}
    return {
        "evidence_class": "INTERNAL_ADVISORY",
        "report_event_id": event.event_id, "schedule_id": str(schedule_id),
        "scope": report.get("scope"), "status": report.get("status"),
        "observed_at": report.get("observed_at"), "trigger": report.get("trigger"),
        "heimdall_decision": recommendation.get("heimdall_decision"),
        "verified_internal_outcome_ids": [
            entry["outcome_event_id"] for entry in report.get("verified_internal_outcomes", [])
        ],
        "independent_loki_cleared": False, "execution_authorized": False,
    }
