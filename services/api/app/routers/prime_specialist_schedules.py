"""Schedule scoped shadow intelligence using the canonical Prime evaluator."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func, inspect, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.prime_specialist_schedule import PrimeScheduleTrigger, PrimeSpecialistSchedule
from app.routers.completion_registry import (
    UniversalOpportunityBatchIn, UniversalOpportunityIn, _validate_phase3_opportunity,
    evaluate_universal_opportunities,
)
from app.routers.prime_business_factory import require_factory_schema
from app.services.foundry_industry import (
    EVENT_PREFIX as INDUSTRY_PREFIX, INTERNATIONAL_PREFIX, STRATEGY_PREFIX, read_industry_reassessment,
)
from app.services.prime_business_execution import (
    _check_legacy, _emergency_stop_active, _event, require_owner_mandate_key,
    scoped_factory_findings, verified_internal_outcomes,
)

from app.services.foundry_discovery import WITHDRAWAL_PREFIX, verify_withdrawal
from app.services.trade_learning import LESSON_PREFIX, lesson_for_trigger
from app.services.specialist_triggers import outcome_scope_key


REPORT_EVENT = "PRIME_SPECIALIST_SHADOW_REPORT"


def require_schedule_schema(db: Session = Depends(get_db)):
    require_factory_schema(db)
    inspector = inspect(db.get_bind())
    required = ("prime_specialist_schedules", "prime_schedule_triggers", "learning_feedback_records", "knowledge_registry_items")
    if any(not inspector.has_table(name) for name in required):
        raise HTTPException(status_code=503, detail="Specialist scheduling schema not ready")
    columns = {column["name"] for column in inspector.get_columns(PrimeSpecialistSchedule.__tablename__)}
    if not {"outcome_scope_key", "pending_outcome_event_id"} <= columns:
        raise HTTPException(status_code=503, detail="Specialist scheduling schema not ready")


router = APIRouter(
    prefix="/api/prime/specialist-schedules", tags=["prime-specialist-schedules"],
    dependencies=[Depends(require_prime_control_key), Depends(require_schedule_schema)],
)


class ScheduleIn(BaseModel):
    schedule_id: UUID
    business_id: str = Field(min_length=3, max_length=120)
    opportunity: UniversalOpportunityIn
    cadence_seconds: int = Field(ge=300, le=86400, strict=True)
    duration_seconds: int = Field(ge=300, le=2592000, strict=True)
    on_verified_outcome: bool = False
    on_economic_reassessment: bool = False


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _scope(payload: ScheduleIn) -> dict:
    return {
        "legacy_instance_id": payload.opportunity.legacy,
        "business_id": payload.business_id,
        "engine_id": payload.opportunity.engine_id,
        "jurisdiction": payload.opportunity.jurisdiction,
    }


def _lookup(db: Session, schedule_id: UUID) -> PrimeSpecialistSchedule:
    row = db.get(PrimeSpecialistSchedule, schedule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Specialist schedule not found")
    return row


def _report(db: Session, schedule_id: UUID, event_id: str) -> dict | None:
    event = db.query(LegacyOrchestrationEvent).filter_by(event_id=event_id, event_type=REPORT_EVENT).one_or_none()
    report = json.loads(event.payload_json) if event else None
    if not isinstance(report, dict) or report.get("schedule_id") != str(schedule_id):
        return None
    digest = report.get("report_sha256")
    if digest and digest != shadow_report_digest(event_id, report):
        raise HTTPException(409, "Specialist schedule report failed integrity checks")
    return report


def shadow_report_digest(event_id: str, report: dict) -> str:
    return artifact_digest("prime_specialist_report", event_id, {
        key: value for key, value in report.items() if key != "report_sha256"
    })


def _describe(db: Session, row: PrimeSpecialistSchedule) -> dict:
    report = _report(db, row.id, row.last_report_event_id) if row.last_report_event_id else None
    economic = or_(PrimeScheduleTrigger.event_id.startswith("ECON-"),
                   PrimeScheduleTrigger.event_id.startswith(WITHDRAWAL_PREFIX),
                   PrimeScheduleTrigger.event_id.startswith("DISCOVERY-"),
                   PrimeScheduleTrigger.event_id.startswith("FOL-"))
    queued = db.execute(select(economic, PrimeScheduleTrigger.failure_code, func.count()).where(
        PrimeScheduleTrigger.schedule_id == row.id,
    ).group_by(economic, PrimeScheduleTrigger.failure_code)).all()
    counts = {(is_economic, code): count for is_economic, code, count in queued}
    return {
        "schedule_id": row.id,
        "queued_outcome_count": counts.pop((False, None), 0) + int(row.pending_outcome_event_id is not None),
        "queued_economic_count": counts.pop((True, None), 0),
        "failed_outcome_counts": {code: count for (is_economic, code), count in counts.items() if not is_economic},
        "failed_economic_counts": {code: count for (is_economic, code), count in counts.items() if is_economic},
        "state": "expired" if row.state == "active" and row.expires_at <= _utc_now() else row.state,
        "next_due_at": row.next_due_at.replace(tzinfo=timezone.utc),
        "expires_at": row.expires_at.replace(tzinfo=timezone.utc),
        "latest_report": report,
        "on_verified_outcome": row.request.get("on_verified_outcome", False),
        "on_economic_reassessment": row.request.get("on_economic_reassessment", False),
    }


@router.post("", status_code=201, dependencies=[Depends(require_owner_mandate_key)])
def create_schedule(payload: ScheduleIn, db: Session = Depends(get_db)):
    opportunity = payload.opportunity
    if not opportunity.jurisdiction or opportunity.replay_partition or opportunity.historical_outcome is not None:
        raise HTTPException(status_code=422, detail="Supply a current opportunity in a registered jurisdiction")
    if not opportunity.human_approval_required or opportunity.independent_loki_review_id is not None:
        raise HTTPException(status_code=422, detail="Schedule requires human approval and carries no independent review")
    _validate_phase3_opportunity(opportunity)
    normalized = payload.model_copy(update={
        "opportunity": opportunity.model_copy(update={
            "persist_decision": False, "specialist_inputs": {**opportunity.specialist_inputs, "business_id": payload.business_id},
        }),
    })
    request = normalized.model_dump(mode="json")
    if len(json.dumps(request).encode("utf-8")) > 65536:
        raise HTTPException(status_code=413, detail="Schedule inputs exceed 64 KiB")
    _check_legacy(db, **_scope(normalized))
    now = _utc_now()
    row = PrimeSpecialistSchedule(
        id=payload.schedule_id, request=request, cadence_seconds=payload.cadence_seconds,
        next_due_at=now, expires_at=now + timedelta(seconds=payload.duration_seconds), state="active",
        outcome_scope_key=outcome_scope_key(_scope(normalized)) if (payload.on_verified_outcome or payload.on_economic_reassessment) else None,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        row = _lookup(db, payload.schedule_id)
        if {"on_verified_outcome": False, "on_economic_reassessment": False, **row.request} != request:
            raise HTTPException(status_code=409, detail="Schedule ID already has a different mandate")
    return _describe(db, row)


@router.get("/{schedule_id}")
def read_schedule(schedule_id: UUID, db: Session = Depends(get_db)):
    return _describe(db, _lookup(db, schedule_id))


@router.get("/{schedule_id}/reports/{report_event_id}")
def read_report(schedule_id: UUID, report_event_id: str, db: Session = Depends(get_db)):
    report = _report(db, schedule_id, report_event_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Specialist report not found")
    return report


@router.delete("/{schedule_id}", dependencies=[Depends(require_owner_mandate_key)])
def cancel_schedule(schedule_id: UUID, db: Session = Depends(get_db)):
    _lookup(db, schedule_id)
    db.execute(update(PrimeSpecialistSchedule).where(PrimeSpecialistSchedule.id == schedule_id).values(state="cancelled"))
    db.commit()
    return _describe(db, _lookup(db, schedule_id))


def attach_operating_reassessment(db, payload, scope, today, outcomes, report):
    from app.routers.foundry_checkout import scoped_checkout_learning
    from app.services.checkout_operating_signals import checkout_operating_blockers
    from app.services.treasury_reconciliation import observe_statement_heads
    from app.services.economic_control import specialist_economics
    from app.services.foundry_discovery import economic_blockers, economics, require_current_candidate

    opportunity = payload.opportunity
    inputs = opportunity.specialist_inputs
    listing = inputs.get("proposed_internal_listing")
    artifact_id = listing.get("artifact_id") if isinstance(listing, dict) else None
    checkout = scoped_checkout_learning(db, scope, outcomes, artifact_id=artifact_id if isinstance(artifact_id, str) else None)
    capital = specialist_economics(db, "HEIMDALL", scope, today).get("economic_reassessment")
    blockers = set(capital["blockers"] if capital else ())
    if any(row["opportunity_id"] == opportunity.opportunity_id
           for row in report.get("source_revision", {}).get("affected_decisions", ())):
        blockers.add("PRIOR_DECISION_SOURCE_REVISED")
    if capital is None:
        from app.heimdall.authority import is_live
        from app.services.stripe_bank_booking import scoped_bank_blockers

        blockers.update(scoped_bank_blockers(db, scope, live=is_live()))
    source_assessment = None
    if inputs.get("foundry_evidence") or opportunity.source == "scoped_foundry_evidence":
        try:
            evidence = require_current_candidate(db, opportunity.model_dump(mode="json"), scope, today, advisory_only=True)
        except HTTPException as exc:
            if exc.status_code != 409:
                raise
            blockers.add("FOUNDRY_SOURCE_NO_LONGER_CURRENT")
        else:
            projected = economics(evidence)
            source_assessment = {"kind": evidence.kind, "economics": projected,
                                 "source_ref": evidence.source_ref, "evidence_class": evidence.evidence_class}
            blockers.update(economic_blockers(evidence.kind, projected))
    blockers.update(checkout_operating_blockers(checkout))
    factory_findings = scoped_factory_findings(db, scope, outcomes)["contradictions"]
    blockers.update(item["code"] for item in factory_findings)
    treasury = observe_statement_heads(db, scope)
    if any(row["status"] == "EVIDENCE_CONFLICT" for row in treasury.get("accounts", [])):
        blockers.add("TREASURY_STATEMENT_EVIDENCE_CONFLICT")
    from app.heimdall.authority import is_live
    from app.services.stripe_recurring import scoped_subscription_outcomes
    from app.services.stripe_revenue_release import scoped_delivery_outcomes

    paid_outcomes = scoped_delivery_outcomes(db, scope, live=is_live())
    if any(item["status"] in {"DELIVERY_REVIEW_REQUIRED", "DELIVERY_EVIDENCE_CONFLICT"} for item in paid_outcomes):
        blockers.add("PAID_DELIVERY_EVIDENCE_REVIEW_REQUIRED")
    recurring = scoped_subscription_outcomes(db, scope, live=is_live())
    if recurring and recurring["status"] == "REVIEW_REQUIRED":
        blockers.add("RECURRING_PAYMENT_EVIDENCE_REVIEW_REQUIRED")
    trade = report.get("trade_reassessment")
    if trade:
        blockers.add("INDUSTRY_DEMAND_UNVERIFIED")
        for name in ("BASE", "STRESS"):
            blockers.update(trade["skilled_trade"]["scenarios"][name]["blockers"])
    international = report.get("international_reassessment")
    if international:
        blockers.add("INDUSTRY_DEMAND_UNVERIFIED")
        blockers.update(international["international"]["blockers"])
    if report.get("trigger_trade_outcome_id"):
        if not payload.on_economic_reassessment:
            raise HTTPException(409, "Trade outcome reassessment is not enrolled")
        trade_lesson = lesson_for_trigger(capital or {}, report["trigger_trade_outcome_id"])
        if trade_lesson["forecast"]["request"]["opportunity_key"] != opportunity.opportunity_id:
            raise HTTPException(409, "Trade lesson belongs to a different opportunity")
        blockers.update(trade_lesson["lesson"]["blockers"])
        report["trade_learning"] = trade_lesson
    strategies = next((item for item in (capital or {}).get("business_strategy_assessments", ())
                       if item["opportunity_key"] == opportunity.opportunity_id), None)
    trigger_strategy = report.get("strategy_reassessment")
    if trigger_strategy and (not strategies or strategies["evidence_id"] != trigger_strategy["evidence_id"]):
        raise HTTPException(409, "Strategy trigger lacks a current comparison for this scheduled opportunity")
    if strategies is not None:
        report["business_strategy_proposal"] = strategies
        blockers.add("STRATEGY_PROPOSAL_REQUIRES_INDEPENDENT_REVIEW_AND_AUTHORITY")
    recommendation = report["recommendation"]
    if checkout or capital or source_assessment or treasury.get("accounts") or blockers or paid_outcomes or recurring:
        report["operating_reassessment"] = {
            "checkout_learning": checkout, "economic_reassessment": capital,
            "source_assessment": source_assessment, "blockers": sorted(blockers),
            "external_authority": False, "prior_recommendation": recommendation["heimdall_decision"],
        }
    if paid_outcomes:
        report["operating_reassessment"]["paid_delivery_outcomes"] = paid_outcomes
    if recurring:
        report["operating_reassessment"]["recurring_paid_periods"] = recurring
    if treasury.get("accounts"):
        report["operating_reassessment"]["treasury_statement_evidence"] = treasury
    if factory_findings:
        report["operating_reassessment"]["factory_evidence_contradictions"] = factory_findings
    if blockers:
        report["recommendation"] = {**recommendation, "heimdall_decision": "HOLD", "best_option_right_now": None,
                                    "abstain": True, "message": "Hold for review of the scoped operating evidence.",
                                    "details": {"blockers": sorted(blockers)}}


def run_due_schedule(db: Session, *, now: datetime | None = None) -> dict:
    """Run one due slot. A report and cursor advance commit as one transaction."""
    require_schedule_schema(db)
    if _emergency_stop_active(db):
        return {"status": "blocked", "emergency_stop": True}
    now = now if now is not None else _utc_now()
    oldest = select(func.min(PrimeScheduleTrigger.queued_at)).where(
        PrimeScheduleTrigger.schedule_id == PrimeSpecialistSchedule.id,
        PrimeScheduleTrigger.failure_code.is_(None),
    ).scalar_subquery()
    row = (
        db.query(PrimeSpecialistSchedule)
        .filter_by(state="active")
        .filter(
            PrimeSpecialistSchedule.expires_at > now,
            or_(PrimeSpecialistSchedule.next_due_at <= now,
                PrimeSpecialistSchedule.pending_outcome_event_id.is_not(None), oldest.is_not(None)),
        )
        .order_by((PrimeSpecialistSchedule.next_due_at <= now).desc(),
                  func.coalesce(oldest, PrimeSpecialistSchedule.next_due_at), PrimeSpecialistSchedule.id)
        .with_for_update(skip_locked=True, key_share=True)
        .first()
    )
    if row is None:
        return {"status": "idle"}
    # Coalesce missed slots after downtime. Preserve the original cadence.
    timed = row.next_due_at <= now
    legacy_outcome = row.pending_outcome_event_id
    queued = db.scalar(select(PrimeScheduleTrigger).where(
        PrimeScheduleTrigger.schedule_id == row.id, PrimeScheduleTrigger.failure_code.is_(None),
    ).order_by(PrimeScheduleTrigger.queued_at, PrimeScheduleTrigger.event_id).limit(1)) if legacy_outcome is None else None
    event_id = legacy_outcome or (queued.event_id if queued is not None else None)
    economic_id = event_id if queued is not None and event_id.startswith("ECON-") else None
    withdrawal_id = event_id if queued is not None and event_id.startswith(WITHDRAWAL_PREFIX) else None
    revision_id = event_id if queued is not None and event_id.startswith("DISCOVERY-") else None
    learning_id = event_id if queued is not None and event_id.startswith("FOL-") else None
    industry_id = event_id if queued is not None and event_id.startswith(INDUSTRY_PREFIX) else None
    trade_lesson_id = event_id if queued is not None and event_id.startswith(LESSON_PREFIX) else None
    international_id = event_id if queued is not None and event_id.startswith(INTERNATIONAL_PREFIX) else None
    strategy_id = event_id if queued is not None and event_id.startswith(STRATEGY_PREFIX) else None
    outcome_id = None if any((economic_id, withdrawal_id, revision_id, learning_id, industry_id, international_id,
                              trade_lesson_id, strategy_id)) else event_id
    trigger_field = ("trigger_source_withdrawal_id" if withdrawal_id else
                     "trigger_operating_lesson_id" if learning_id else
                     "trigger_skilled_trade_id" if industry_id else
                     "trigger_trade_outcome_id" if trade_lesson_id else
                     "trigger_international_id" if international_id else
                     "trigger_strategy_id" if strategy_id else
                     "trigger_source_revision_id" if revision_id else
                     "trigger_economic_event_id" if economic_id else "trigger_outcome_event_id")
    elapsed_slots = (now - row.next_due_at) // timedelta(seconds=row.cadence_seconds) if timed else 0
    slot = row.next_due_at.replace(tzinfo=timezone.utc).isoformat() if timed else None
    occurrence = event_id or slot
    report_id = "SPECIALIST-" + hashlib.sha256(f"{row.id}/{occurrence}".encode()).hexdigest()
    payload = ScheduleIn.model_validate(row.request)
    scope = _scope(payload)
    if event_id:
        existing = db.scalar(select(LegacyOrchestrationEvent).where(
            LegacyOrchestrationEvent.event_id == report_id,
        ))
        if existing is not None:
            try:
                previous = json.loads(existing.payload_json or "null")
            except ValueError:
                previous = None
            if (existing.event_type != REPORT_EVENT or existing.legacy_instance_id != scope["legacy_instance_id"]
                    or not isinstance(previous, dict) or previous.get("scope") != scope
                    or previous.get("schedule_id") != str(row.id)
                    or previous.get(trigger_field) != event_id
                    or previous.get("report_sha256") != shadow_report_digest(report_id, previous)):
                if queued is None:
                    raise HTTPException(409, "Prior specialist outcome report failed integrity checks")
                queued.failure_code = "EXISTING_REPORT_INTEGRITY_FAILED"
                db.commit()
                return {"status": "blocked", "failure_code": queued.failure_code}
            if queued is not None:
                db.delete(queued)
            else:
                row.pending_outcome_event_id = None
            db.commit()
            return {"status": "replayed", "report_event_id": report_id}
    report = {
        "schedule_id": str(row.id), "report_event_id": report_id, "scheduled_for": slot,
        "observed_at": now.replace(tzinfo=timezone.utc).isoformat(), "scope": scope,
        "external_authority": False, "independent_loki_cleared": False,
        "effect": "ADVISORY_ONLY", "missed_slots_coalesced": elapsed_slots,
        "trigger": "VERIFIED_OUTCOME" if outcome_id else "CADENCE",
        "trigger_outcome_event_id": outcome_id,
    }
    if economic_id:
        report.update(trigger="ECONOMIC_REASSESSMENT", trigger_economic_event_id=economic_id)
    if withdrawal_id:
        report.update(trigger="FOUNDRY_SOURCE_WITHDRAWN", trigger_source_withdrawal_id=withdrawal_id)
    if revision_id:
        report.update(trigger="FOUNDRY_SOURCE_REVISED", trigger_source_revision_id=revision_id)
    if learning_id:
        report.update(trigger="OPERATING_LESSON", trigger_operating_lesson_id=learning_id)
    if industry_id:
        report.update(trigger="SKILLED_TRADE_REASSESSMENT", trigger_skilled_trade_id=industry_id)
    if trade_lesson_id:
        report.update(trigger="TRADE_OPERATING_OUTCOME", trigger_trade_outcome_id=trade_lesson_id)
    if international_id:
        report.update(trigger="INTERNATIONAL_REASSESSMENT", trigger_international_id=international_id)
    if strategy_id:
        report.update(trigger="BUSINESS_STRATEGY_REASSESSMENT", trigger_strategy_id=strategy_id)
    try:
        _check_legacy(db, **scope)
        if strategy_id:
            if not payload.on_economic_reassessment:
                raise HTTPException(409, "Business strategy reassessment is not enrolled")
            report["strategy_reassessment"] = read_industry_reassessment(db, strategy_id, scope, now.date(), strategies=True)
        if industry_id or international_id:
            if not payload.on_economic_reassessment:
                raise HTTPException(409, "Industry reassessment is not enrolled")
            if international_id:
                report["international_reassessment"] = read_industry_reassessment(
                    db, international_id, scope, now.date(), international=True,
                )
            else:
                report["trade_reassessment"] = read_industry_reassessment(db, industry_id, scope, now.date())
        if withdrawal_id and (not payload.on_economic_reassessment or not verify_withdrawal(db, scope, withdrawal_id)):
            raise HTTPException(409, "Foundry source withdrawal could not be revalidated")
        if economic_id:
            from app.services.economic_control import ready as economic_ready, verify_trigger

            if (not payload.on_economic_reassessment or not economic_ready(db)
                    or not verify_trigger(db, scope, economic_id)):
                raise HTTPException(409, "Economic trigger evidence failed revalidation")
        if revision_id:
            from app.services.foundry_intake import source_revision

            if not payload.on_economic_reassessment:
                raise HTTPException(409, "Source reassessment is not enrolled")
            report["source_revision"] = source_revision(db, revision_id, scope, now.date())
        if learning_id:
            from app.routers.foundry_operating_rehearsal import verify_operating_trigger

            if not payload.on_economic_reassessment:
                raise HTTPException(409, "Operating learning reassessment is not enrolled")
            report["operating_lesson"] = verify_operating_trigger(db, scope, learning_id)
        outcomes = verified_internal_outcomes(db, **scope, trigger_event_id=outcome_id)
        if outcome_id and not any(item["outcome_event_id"] == outcome_id for item in outcomes):
            raise HTTPException(status_code=409, detail="Trigger outcome evidence failed revalidation")
        result = evaluate_universal_opportunities(UniversalOpportunityBatchIn(
            opportunities=[payload.opportunity], shadow_mode=True, persist_decision=False,
        ), db)
        recommendation = result["owner_recommendation"]
        report.update(status="evaluated", evaluation=result["evaluations"][0], recommendation=recommendation,
                      verified_internal_outcomes=outcomes)
        attach_operating_reassessment(db, payload, scope, now.date(), outcomes, report)
    except (HTTPException, ValidationError) as exc:
        report.update(status="blocked", reason=exc.detail if isinstance(exc, HTTPException) else "Invalid specialist inputs")
    report = jsonable_encoder(report)
    report["report_sha256"] = shadow_report_digest(report_id, report)
    _event(
        db, event_id=report_id, legacy_instance_id=scope["legacy_instance_id"], event_type=REPORT_EVENT,
        message=f"Prime specialist schedule {report['status']}", payload=report,
    )
    if timed:
        row.next_due_at += timedelta(seconds=(elapsed_slots + 1) * row.cadence_seconds)
    if queued is not None:
        db.delete(queued)
    elif legacy_outcome:
        row.pending_outcome_event_id = None
    row.last_report_event_id = report_id
    db.commit()
    return {"status": report["status"], "report_event_id": report_id}
