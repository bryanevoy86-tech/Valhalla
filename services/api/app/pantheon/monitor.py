"""Run one local role assignment without invoking the Prime evaluator."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, inspect, or_, select
from sqlalchemy.orm import Session

from app.loki.review_service import artifact_digest
from app.models.completion_registry import EngineRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.norns_forecast import NornsForecast, NornsHoldout
from app.models.specialist_assignment import SpecialistAssignment, SpecialistTrigger
from app.pantheon.roles import LENSES
from app.pantheon.forecasts import calibration_measurements, issue_scoped_estimate, sweep_scoped_outcomes
from app.services.foundry_discovery import DISCOVERY_ROLES, WITHDRAWAL_PREFIX, discover, verify_withdrawal
from app.services.foundry_intake import verify_intake_trigger
from app.services.market_intelligence import market_observations
from app.services.economic_control import ready as economic_ready, specialist_economics, verify_trigger
from app.services.prime_business_execution import (
    _approval_id, _check_legacy, _emergency_stop_active, _event, scoped_factory_findings, verified_internal_outcomes,
)


REPORT_EVENT = "PANTHEON_ASSIGNMENT_REPORT"


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def assignment_schema(db: Session):
    schema = inspect(db.connection())
    if not all(schema.has_table(model.__tablename__) for model in (SpecialistAssignment, SpecialistTrigger)):
        raise HTTPException(503, "Specialist assignment schema not ready")


def observations(db: Session, lens: str, scope: dict, outcomes: list[dict], now, cadence: int, *, forecast_after=None) -> dict:
    work = LegacyInstanceWorkItem
    scope_filter = [getattr(work, field) == value for field, value in scope.items()]
    if lens == "verified_learning":
        return {"verified_internal_outcomes": [item["outcome_event_id"] for item in outcomes],
                "commercial_performance_verified": False}
    if lens == "engine_readiness":
        schema = inspect(db.connection())
        if not schema.has_table(EngineRegistryItem.__tablename__):
            return {"evidence_status": "REGISTRY_UNAVAILABLE"}
        row = db.scalar(select(EngineRegistryItem).filter_by(
            engine_id=scope["engine_id"], legacy_instance_id=scope["legacy_instance_id"],
        ))
        return {
            "engine_id": scope["engine_id"], "registry_state": row.current_state if row else None,
            "audit_state": row.audit_state if row else None,
            "evidence_status": "RECORDED_REGISTRY_STATE" if row else "NO_SCOPED_ENGINE_RECORD",
            "market_opportunities_verified": False,
        }
    if lens == "forecast_outcomes":
        schema = inspect(db.connection())
        if any(not schema.has_table(model.__tablename__) for model in (NornsForecast, NornsHoldout)):
            return {"evidence_status": "FORECAST_SCHEMA_UNAVAILABLE"}
        if "estimate_source" not in {item["name"] for item in schema.get_columns(NornsForecast.__tablename__)}:
            return {"evidence_status": "FORECAST_SCHEMA_UNAVAILABLE"}
        sweep = sweep_scoped_outcomes(db, scope, now, after=forecast_after)
        return {**calibration_measurements(db, now, scope=scope, horizon_seconds=cadence),
                "outcome_resolution": sweep,
                "score_cohort": "ORDINARY_INTERNAL_ESTIMATE_SOURCES",
                "target": "VERIFIED_INTERNAL_ARTIFACT_BY_DEADLINE",
                **issue_scoped_estimate(db, scope, now, cadence)}

    counts = dict(db.execute(select(work.status, func.count()).where(*scope_filter).group_by(work.status)).all())
    actions = db.scalars(select(work.action_id).where(*scope_filter).order_by(work.id.desc()).limit(20)).all()
    if lens == "approval_evidence":
        events = db.scalars(select(LegacyOrchestrationEvent.event_id).where(
            LegacyOrchestrationEvent.event_id.in_([_approval_id(action) for action in actions]),
            LegacyOrchestrationEvent.event_type == "FACTORY_OWNER_APPROVED",
            LegacyOrchestrationEvent.legacy_instance_id == scope["legacy_instance_id"],
        )).all()
        return {"reviewed_action_ids": actions, "recorded_approval_event_ids": list(events),
                "scope_authority_confirmed": False}
    if lens == "counter_evidence":
        return {"work_status_counts": counts, "recent_work_ids": list(actions),
                "verified_internal_outcome_ids": [item["outcome_event_id"] for item in outcomes],
                "independent_review_required_for_material_execution": True}
    stalled_filter = (*scope_filter, work.status.in_(("queued", "approved", "running")),
                      work.updated_at < now - timedelta(seconds=cadence))
    stalled_count = db.scalar(select(func.count()).select_from(work).where(*stalled_filter))
    oldest = db.scalars(select(work.action_id).where(*stalled_filter)
                        .order_by(work.updated_at, work.id).limit(10)).all()
    return {"work_status_counts": counts, "recent_work_ids": list(actions),
            "stalled_work": {"count": stalled_count, "oldest_action_ids": list(oldest),
                             "age_threshold_seconds": cadence,
                             "basis": "AGE_SINCE_LAST_RECORDED_WORK_UPDATE"}}


def run_assignment(db: Session, role: str, *, now=None) -> dict:
    if role not in LENSES:
        raise ValueError("Unknown specialist role")
    assignment_schema(db)
    if _emergency_stop_active(db):
        return {"status": "blocked", "emergency_stop": True}
    now = now or utc_now()
    oldest_queued = select(func.min(SpecialistTrigger.queued_at)).where(
        SpecialistTrigger.assignment_id == SpecialistAssignment.id,
        SpecialistTrigger.failure_code.is_(None),
    ).scalar_subquery()
    assignment = db.scalar(select(SpecialistAssignment).where(
        SpecialistAssignment.role == role,
        SpecialistAssignment.state == "active", SpecialistAssignment.expires_at > now,
        or_(SpecialistAssignment.next_due_at <= now, SpecialistAssignment.pending_event_id.is_not(None), oldest_queued.is_not(None)),
    ).order_by((SpecialistAssignment.next_due_at <= now).desc(),
               func.coalesce(oldest_queued, SpecialistAssignment.next_due_at), SpecialistAssignment.id)
        .with_for_update(skip_locked=True, key_share=True).limit(1))
    if assignment is None:
        return {"status": "idle"}
    legacy_event = assignment.pending_event_id
    queued = db.scalar(select(SpecialistTrigger).where(
        SpecialistTrigger.assignment_id == assignment.id, SpecialistTrigger.failure_code.is_(None),
    ).order_by(SpecialistTrigger.queued_at, SpecialistTrigger.event_id).limit(1)) if legacy_event is None else None
    event = legacy_event or (queued.event_id if queued is not None else None)
    due = assignment.next_due_at <= now
    economic_event = bool(event and event.startswith("ECON-"))
    discovery_event = bool(event and event.startswith("DISCOVERY-"))
    withdrawal_event = bool(event and event.startswith(WITHDRAWAL_PREFIX))
    trigger_type = ("FOUNDRY_SOURCE_WITHDRAWN" if withdrawal_event else
                    "ECONOMIC_REASSESSMENT" if economic_event else "SOURCE_DISCOVERY" if discovery_event
                    else "VERIFIED_OUTCOME" if event else "CADENCE")
    material = f"{assignment.id}/{event or assignment.next_due_at.isoformat()}"
    event_id = "GOD-" + hashlib.sha256(material.encode()).hexdigest()
    if event:
        try:
            previous = verified_report(db, event_id)
        except HTTPException as exc:
            if exc.status_code != 404:
                if exc.status_code != 409 or queued is None:
                    raise
                queued.failure_code = "EXISTING_REPORT_INTEGRITY_FAILED"
                db.commit()
                return {"status": "blocked", "failure_code": queued.failure_code}
        else:
            if (previous.get("assignment_id"), previous.get("role"), previous.get("scope"),
                previous.get("trigger"), previous.get("trigger_event_id")) != (
                str(assignment.id), role, assignment.scope, trigger_type, event,
            ):
                if queued is None:
                    raise HTTPException(409, "Specialist event replay scope does not match")
                queued.failure_code = "EXISTING_REPORT_SCOPE_MISMATCH"
                db.commit()
                return {"status": "blocked", "failure_code": queued.failure_code}
            if queued is not None:
                db.delete(queued)
            else:
                assignment.pending_event_id = None
            db.commit()
            return {"status": "replayed", "report_event_id": event_id}

    cadence = timedelta(seconds=assignment.cadence_seconds)
    elapsed_slots = (now - assignment.next_due_at) // cadence + 1 if due else 0
    report = {
        "report_event_id": event_id, "assignment_id": str(assignment.id), "role": role,
        "lens": LENSES[role], "scope": assignment.scope, "observed_at": now.isoformat() + "Z",
        "trigger": trigger_type, "trigger_event_id": event,
        "cadence": {
            "scheduled_for": assignment.next_due_at.isoformat() + "Z" if due else None,
            "slots_elapsed": elapsed_slots,
            "missed_slots": max(0, elapsed_slots - 1),
        },
        "model_used": False, "external_authority": False, "independent_review_authority": False,
    }
    try:
        _check_legacy(db, **assignment.scope)
        outcome_trigger = event if not (withdrawal_event or economic_event or discovery_event) else None
        outcomes = verified_internal_outcomes(db, **assignment.scope, trigger_event_id=outcome_trigger)
        if economic_event and (not economic_ready(db) or not verify_trigger(db, assignment.scope, event)):
            raise HTTPException(409, "Economic evidence trigger could not be revalidated")
        if discovery_event and not verify_intake_trigger(db, event, assignment.scope, now.date()):
            raise HTTPException(409, "Discovery evidence trigger could not be revalidated")
        if withdrawal_event and not verify_withdrawal(db, assignment.scope, event):
            raise HTTPException(409, "Foundry source withdrawal could not be revalidated")
        if outcome_trigger and not any(
            item["outcome_event_id"] == outcome_trigger for item in outcomes
        ):
            raise HTTPException(409, "Trigger receipt could not be revalidated")
        forecast_after = None
        if role == "NORNS" and assignment.last_report_event_id:
            try:
                prior = verified_report(db, assignment.last_report_event_id)
                if (prior.get("assignment_id"), prior.get("role"), prior.get("scope")) == (
                    str(assignment.id), role, assignment.scope,
                ):
                    cursor = prior.get("observations", {}).get("outcome_resolution", {}).get("next_after")
                    forecast_after = UUID(cursor) if cursor else None
            except (HTTPException, ValueError, TypeError, AttributeError):
                # An untrusted cursor can only restart the scan.
                pass
        facts = observations(db, LENSES[role], assignment.scope, outcomes, now, assignment.cadence_seconds,
                             forecast_after=forecast_after)
        if role in DISCOVERY_ROLES:
            facts.update(discover(db, role, assignment.scope, now.date()))
        if role in {"FREYJA", "BRAGI", "ODIN", "HUGINN", "NJORD", "NORNS", "TYR", "LOKI", "HEIMDALL", "MIMIR"}:
            from app.services.acquisition_comparison import observe_reviewed_comparisons
            from app.services.acquisition_rehearsal import observe_scoped_acquisition

            acquisition = observe_scoped_acquisition(db, assignment.scope)
            if acquisition:
                facts["acquisition_rehearsal"] = acquisition
            reviewed_acquisition = observe_reviewed_comparisons(db, assignment.scope)
            if reviewed_acquisition:
                facts["reviewed_acquisition_history"] = reviewed_acquisition
        facts.update(market_observations(db, role, assignment.scope, now))
        if role in {"MIMIR", "NJORD", "HEIMDALL", "FORSETI", "LOKI", "TYR", "NORNS"}:
            from app.routers.foundry_checkout import scoped_checkout_learning

            from app.heimdall.authority import is_live
            from app.services.stripe_revenue_release import scoped_delivery_outcomes

            paid_outcomes = scoped_delivery_outcomes(db, assignment.scope, live=is_live())
            if paid_outcomes:
                facts["paid_delivery_outcomes"] = paid_outcomes
            checkout = scoped_checkout_learning(db, assignment.scope, outcomes)
            if checkout:
                facts["checkout_learning"] = checkout
        if role == "HEIMDALL" or LENSES[role] in {"approval_evidence", "counter_evidence", "verified_learning"}:
            facts["factory_evidence_reconciliation"] = scoped_factory_findings(db, assignment.scope, outcomes)
        if role in {"NJORD", "FORSETI", "MIMIR", "HEIMDALL"}:
            from app.services.treasury_reconciliation import observe_statement_heads

            facts["treasury_statement_evidence"] = observe_statement_heads(db, assignment.scope)
        facts.update(specialist_economics(db, role, assignment.scope, now.date()))
        report.update(status="observed", observations=facts)
    except HTTPException as exc:
        report.update(status="blocked", reason=exc.detail)
    report["report_sha256"] = artifact_digest("pantheon_report", event_id, report)
    _event(db, event_id=event_id, legacy_instance_id=assignment.scope["legacy_instance_id"],
           event_type=REPORT_EVENT, message="Local specialist assignment observed", payload=report)
    assignment.last_report_event_id = event_id
    if queued is not None:
        db.delete(queued)
    elif legacy_event:
        assignment.pending_event_id = None
    if due:
        assignment.next_due_at += cadence * elapsed_slots
    db.commit()
    return {"status": report["status"], "report_event_id": event_id}


def verified_report(db: Session, event_id: str) -> dict:
    event = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=event_id, event_type=REPORT_EVENT))
    if event is None:
        raise HTTPException(404, "Specialist report not found")
    try:
        report = json.loads(event.payload_json)
        digest = report.pop("report_sha256")
        if (report["report_event_id"] != event_id or report["scope"]["legacy_instance_id"] != event.legacy_instance_id
                or digest != artifact_digest("pantheon_report", event_id, report)):
            raise ValueError
    except (ValueError, TypeError, KeyError, AttributeError):
        raise HTTPException(409, "Specialist report integrity check failed") from None
    return {**report, "report_sha256": digest}


def report_matches_assignment(assignment: SpecialistAssignment | None, report: dict) -> bool:
    return assignment is not None and (
        str(assignment.id), assignment.last_report_event_id, assignment.role, assignment.scope,
    ) == (report.get("assignment_id"), report.get("report_event_id"), report.get("role"), report.get("scope"))
