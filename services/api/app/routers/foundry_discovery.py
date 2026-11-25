"""Intake owner-authorized Foundry evidence and prepare research candidates."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent, SourceRegistryItem
from app.models.foundry_evidence import FoundryEvidence
from app.pantheon.monitor import verified_report
from app.services.foundry_discovery import (
    DISCOVERY_ROLES, EvidenceIn, SCOPE_FIELDS, candidate_fields, checked_evidence, withdrawal_trigger,
)
from app.services.foundry_intake import FoundryIntakeJob, Intake, current_time, intake_ready, job_view, key_for, source_for
from app.services import foundry_industry, trade_learning
from app.services.prime_business_execution import _check_legacy, _event, _json, require_owner_mandate_key
from app.services.consumer_evidence import ConsumerEvidence, EVENT, build_record, event_id, project, read_consumer_evidence
from app.services.specialist_triggers import enqueue_prime, enqueue_research, outcome_scope_key


def schema(db: Session = Depends(get_db)):
    if not inspect(db.connection()).has_table(FoundryEvidence.__tablename__):
        raise HTTPException(503, "Foundry evidence schema unavailable")


router = APIRouter(prefix="/api/prime/foundry", tags=["foundry-discovery"],
                   dependencies=[Depends(require_prime_control_key), Depends(schema)])
owner = [Depends(require_owner_mandate_key)]


@router.post("/evidence", status_code=201, dependencies=owner)
def record_evidence(request: EvidenceIn, db: Session = Depends(get_db)):
    scope = request.model_dump(include=SCOPE_FIELDS)
    _check_legacy(db, **scope)
    if request.observed_on > datetime.now(timezone.utc).date():
        raise HTTPException(422, "Observed date is in the future")
    # Preserve the exact payload shape and digest of historical records without acquisition terms.
    if request.provenance is not None:
        raise HTTPException(422, "Discovery provenance is assigned by the intake worker")
    payload = request.model_dump(mode="json", exclude_none=True)
    digest = artifact_digest("foundry_evidence", str(request.evidence_id), payload)
    row = db.get(FoundryEvidence, request.evidence_id)
    if row:
        if row.digest != digest:
            raise HTTPException(409, "Foundry evidence ID already used")
        return {"evidence_id": row.id, "sha256": row.digest, "revoked": row.revoked}
    row = FoundryEvidence(id=request.evidence_id, scope_key=outcome_scope_key(scope),
                          source_ref=request.source_ref, observed_on=request.observed_on,
                          expires_on=request.expires_on, payload=payload, digest=digest)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Foundry evidence ID or observation already used") from None
    return {"evidence_id": row.id, "sha256": row.digest, "revoked": row.revoked}


@router.delete("/evidence/{evidence_id}", dependencies=owner)
def revoke_evidence(evidence_id: UUID, db: Session = Depends(get_db)):
    row = db.get(FoundryEvidence, evidence_id, with_for_update=True)
    if row is None:
        raise HTTPException(404, "Foundry evidence not found")
    if not row.revoked:
        row.revoked = True
        at = current_time().replace(tzinfo=None)
        event = withdrawal_trigger(row)
        enqueue_research(db, row.scope_key, event, at, roles=DISCOVERY_ROLES)
        enqueue_prime(db, row.scope_key, event, at, subscription="on_economic_reassessment")
        db.commit()
    return {"evidence_id": row.id, "revoked": True}


@router.get("/reports/{report_id}/candidate/{evidence_id}")
def prepare_candidate(report_id: str, evidence_id: UUID, db: Session = Depends(get_db)):
    report = verified_report(db, report_id)
    row = db.get(FoundryEvidence, evidence_id)
    if row is None or not any(
        signal["evidence_id"] == str(evidence_id) and signal["sha256"] == row.digest
        for signal in report.get("observations", {}).get("foundry_signals", [])
    ):
        raise HTTPException(404, "Report does not contain this research candidate")
    _check_legacy(db, **report["scope"])
    payload = checked_evidence(row, report["scope"], datetime.now(timezone.utc).date(), db=db)
    today = datetime.now(timezone.utc).date()
    research = read_consumer_evidence(db, row, payload, report["scope"], today)
    industry = foundry_industry.read_industry(db, row, payload, report["scope"], today)
    signal = next(signal for signal in report["observations"]["foundry_signals"]
                  if signal["evidence_id"] == str(evidence_id) and signal["sha256"] == row.digest)
    if signal.get("consumer_research") != research or signal.get("industry_diligence") != industry:
        raise HTTPException(409, "Run a current specialist report before using revised research")
    return {"proposal": {**candidate_fields(row, payload, report_id, consumer_research=research,
                                            industry_diligence=industry), "persist_decision": False},
            "state": "RESEARCH_CANDIDATE", "execution_authorized": False}


@router.post("/evidence/{evidence_id}/industry-diligence", status_code=201, dependencies=owner)
def record_industry(evidence_id: UUID, request: foundry_industry.IndustryDiligence, db: Session = Depends(get_db)):
    scope = request.scope.model_dump()
    _check_legacy(db, **scope)
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Industry diligence journal unavailable")
    row = db.get(FoundryEvidence, evidence_id, with_for_update=True)
    if row is None:
        raise HTTPException(404, "Foundry evidence not found")
    today = current_time().date()
    evidence = checked_evidence(row, scope, today, db=db)
    result = foundry_industry.build_record(db, row, evidence, scope, request, today)
    reference = foundry_industry.event_id(row.id)
    prior = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=reference))
    if prior is not None:
        if _json(prior.payload_json, {}) != result:
            raise HTTPException(409, "Create a new Foundry evidence version to revise industry diligence")
        return foundry_industry.read_industry(db, row, evidence, scope, today)
    _event(db, event_id=reference, legacy_instance_id=scope["legacy_instance_id"], event_type=foundry_industry.EVENT,
           message="Operating research and execution alternatives recorded", payload=result)
    at = current_time().replace(tzinfo=None)
    enqueue_research(db, row.scope_key, reference, at, roles=DISCOVERY_ROLES)
    if request.skilled_trade is not None:
        enqueue_prime(db, row.scope_key, reference, at, subscription="on_economic_reassessment")
    if request.international is not None:
        enqueue_prime(db, row.scope_key, foundry_industry.INTERNATIONAL_PREFIX + str(row.id), at,
                      subscription="on_economic_reassessment")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Concurrent industry diligence already recorded") from None
    return foundry_industry.project(result, evidence)


def _trade_fixture(db, evidence_id, scope, today):
    from app.models.go_live_state import GoLiveState
    from app.routers.foundry_operating_rehearsal import enabled
    from app.services.prime_business_execution import _emergency_stop_active

    if (not enabled() or not inspect(db.connection()).has_table(GoLiveState.__tablename__)
            or not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__)
            or _emergency_stop_active(db)):
        raise HTTPException(503, "Disposable trade rehearsal is stopped or disabled")
    release = db.get(GoLiveState, 1)
    if release is not None and release.go_live_enabled:
        raise HTTPException(503, "Disposable trade rehearsal cannot run with go-live enabled")
    _check_legacy(db, **scope)
    row = db.get(FoundryEvidence, evidence_id, with_for_update=True, populate_existing=True)
    if row is None:
        raise HTTPException(404, "Trade evidence not found")
    evidence = checked_evidence(row, scope, today, db=db)
    industry = foundry_industry.read_industry(db, row, evidence, scope, today, lock=True)
    if evidence.currency != "CAD" or not (industry or {}).get("skilled_trade"):
        raise HTTPException(409, "Trade rehearsal requires current CAD skilled-trade diligence")
    return row, industry


def _save_trade_event(db, reference, kind, content):
    receipt = trade_learning.sealed(kind, reference, content)
    _event(db, event_id=reference, legacy_instance_id=content["scope"]["legacy_instance_id"],
           event_type=kind, message="Disposable trade learning evidence recorded", payload=receipt)
    return receipt


@router.post("/evidence/{evidence_id}/trade-forecast", status_code=201, dependencies=owner)
def freeze_trade_forecast(evidence_id: UUID, request: trade_learning.ForecastRequest, db: Session = Depends(get_db)):
    from app.loki.models import LokiReview
    from app.loki.review_service import verdict
    from app.routers.economic_control import assess, require_schema

    now = current_time().replace(tzinfo=timezone.utc)
    scope = request.scope.model_dump()
    row, industry = _trade_fixture(db, evidence_id, scope, now.date())
    reference = trade_learning.FORECAST_PREFIX + str(row.id)
    prior = trade_learning.read_record(db, trade_learning.FORECAST_EVENT, reference)
    if prior:
        if (prior["request"] != request.model_dump(mode="json") or prior["evidence_sha256"] != row.digest
                or prior["industry_sha256"] != industry["sha256"]):
            raise HTTPException(409, "Trade forecast replay differs from frozen evidence")
        return prior
    review = db.get(LokiReview, request.independent_review_id)
    if review is None or review.artifact_type != "pantheon_report":
        raise HTTPException(409, "Trade forecast requires an independently reviewed specialist report")
    report = verified_report(db, review.heimdall_reference_id)
    if (report["scope"] != scope or report["role"] not in ("ODIN", "NJORD")
            or report["report_sha256"] != review.artifact_sha256
            or not any(signal.get("evidence_id") == str(row.id) and signal.get("industry_diligence") == industry
                       for signal in report["observations"].get("foundry_signals", ()))):
        raise HTTPException(409, "Trade forecast review must bind the current scoped diligence")
    reviewed = verdict(db, review)
    require_schema(db)
    decision = assess(request.scope, db)
    option = next((item for item in decision["alternatives"] if item["opportunity_key"] == request.opportunity_key
                   and (item.get("foundry_source") or {}).get("evidence_id") == str(row.id)), None)
    if option is None:
        raise HTTPException(409, "Freeze a current scoped Prime trade assessment first")
    trade = industry["skilled_trade"]
    baseline = trade["scenarios"]["BASE"]
    inputs = next(item for item in trade["inputs"]["scenarios"] if item["name"] == "BASE")
    record = {
        "scope": scope, "request": request.model_dump(mode="json"), "evidence_id": str(row.id),
        "evidence_sha256": row.digest, "industry_sha256": industry["sha256"], "opportunity_record_id": option["record_id"],
        "independent_challenge": {"review_id": str(review.id), "artifact_sha256": reviewed.artifact_sha256,
                                  "result_sha256": reviewed.result_sha256, "clearance": reviewed.ok_to_proceed},
        "issued_at": now.isoformat(), "prediction": {
            "expected_contribution_minor": baseline["monthly_operating_contribution_minor"],
            "alternative": {"contribution_minor": trade["scenarios"]["STRESS"]["monthly_operating_contribution_minor"]},
            "deadline_at": (now + timedelta(days=request.horizon_days)).isoformat(),
        },
        "baseline": {
            "completed_jobs": baseline["modeled_jobs_per_month"], "on_site_days_per_job": inputs["on_site_days"],
            "available_skilled_workers": inputs["available_skilled_workers"],
            "callback_cost_minor": inputs["callback_reserve_minor"] * baseline["modeled_jobs_per_month"],
            "payment_days_after_delivery": inputs["payment_days_after_delivery"],
            "required_cash_minor": baseline["startup_cash_reserve_proxy_minor"],
        },
        "decision": {"selection": decision["opportunity_selection"]["decision"],
                     "operating_recommendation": option["operating_recommendation"], "blockers": option["blockers"]},
        "external_authority": False,
    }
    receipt = _save_trade_event(db, reference, trade_learning.FORECAST_EVENT, record)
    db.commit()
    return receipt


@router.post("/evidence/{evidence_id}/trade-outcome", status_code=201, dependencies=owner)
def record_trade_outcome(evidence_id: UUID, request: trade_learning.OutcomeRequest, db: Session = Depends(get_db)):
    now = current_time().replace(tzinfo=timezone.utc)
    scope = request.scope.model_dump()
    row, industry = _trade_fixture(db, evidence_id, scope, now.date())
    forecast = trade_learning.read_record(db, trade_learning.FORECAST_EVENT, trade_learning.FORECAST_PREFIX + str(row.id))
    if (forecast is None or forecast["scope"] != scope or forecast["sha256"] != request.forecast_sha256
            or forecast["evidence_sha256"] != row.digest or forecast["industry_sha256"] != industry["sha256"]):
        raise HTTPException(409, "Trade outcome requires the exact frozen forecast")
    reference = trade_learning.LESSON_PREFIX + str(row.id)
    prior = trade_learning.current_lesson(db, row, scope, industry, forecast["opportunity_record_id"], now.date())
    outcome = request.model_dump(mode="json")
    if prior:
        if prior["lesson"]["outcome"] != outcome:
            raise HTTPException(409, "Trade outcome replay differs from recorded observation")
        return prior["lesson"]
    if not datetime.fromisoformat(forecast["issued_at"]) <= now <= datetime.fromisoformat(forecast["prediction"]["deadline_at"]):
        raise HTTPException(409, "Trade outcome is outside the frozen forecast window")
    lesson = _save_trade_event(db, reference, trade_learning.LESSON_EVENT,
                               trade_learning.project_lesson(forecast, outcome, now.isoformat()))
    at = now.replace(tzinfo=None)
    enqueue_research(db, row.scope_key, reference, at, roles=("MIMIR", "NORNS"))
    enqueue_prime(db, row.scope_key, reference, at, subscription="on_economic_reassessment",
                  opportunity_id=forecast["request"]["opportunity_key"])
    db.commit()
    return lesson


@router.post("/evidence/{evidence_id}/consumer-research", status_code=201, dependencies=owner)
def record_consumer_research(evidence_id: UUID, request: ConsumerEvidence, db: Session = Depends(get_db)):
    scope = request.scope.model_dump()
    _check_legacy(db, **scope)
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Consumer research journal unavailable")
    row = db.get(FoundryEvidence, evidence_id, with_for_update=True)
    if row is None:
        raise HTTPException(404, "Demand evidence not found")
    today = datetime.now(timezone.utc).date()
    evidence = checked_evidence(row, scope, today, db=db)
    result = build_record(row, evidence, scope, request, today)
    reference = event_id(evidence_id)
    recorded = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=reference))
    if recorded is not None:
        if (recorded.event_type != EVENT or recorded.legacy_instance_id != scope["legacy_instance_id"]
                or _json(recorded.payload_json, {}) != result):
            raise HTTPException(409, "Demand observation already has different consumer research")
        return project(result)
    _event(db, event_id=reference, legacy_instance_id=scope["legacy_instance_id"], event_type=EVENT,
           message="Aggregate consumer research recorded", payload=result)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Concurrent consumer research already recorded") from None
    return project(result)


@router.post("/intake", status_code=202, dependencies=owner)
def queue_intake(request: Intake, db: Session = Depends(get_db)):
    return queue_signed_intake(request, db)


def queue_signed_intake(request: Intake, db: Session, *, durable=True):
    if not intake_ready(db):
        raise HTTPException(503, "Discovery intake not migrated")
    now = current_time()
    _check_legacy(db, **request.evidence.model_dump(include=SCOPE_FIELDS))
    source_for(db, request, now.date(), lock=True, verify_enrollment_time=True)
    payload = request.model_dump(mode="json", exclude_none=True)
    job_id = request.evidence.evidence_id
    digest = artifact_digest("foundry_intake", str(job_id), payload)
    prior = db.get(FoundryIntakeJob, job_id)
    if prior is not None:
        if prior.digest != digest:
            raise HTTPException(409, "Discovery job ID already used")
        return job_view(prior)
    observation_key = key_for(request)
    if db.scalar(select(FoundryIntakeJob.id).filter_by(observation_key=observation_key)) is not None:
        raise HTTPException(409, "Source observation already queued")
    job = FoundryIntakeJob(id=job_id, observation_key=observation_key, digest=digest, payload=payload,
                           status="QUEUED", attempts=0, next_attempt_at=now)
    db.add(job)
    try:
        db.commit() if durable else db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Discovery job or source observation already used") from None
    return job_view(job)


@router.get("/intake/{job_id}")
def read_intake(job_id: UUID, db: Session = Depends(get_db)):
    if not intake_ready(db):
        raise HTTPException(503, "Discovery intake not migrated")
    job = db.get(FoundryIntakeJob, job_id)
    if job is None:
        raise HTTPException(404, "Discovery job not found")
    if job.digest != artifact_digest("foundry_intake", str(job.id), job.payload):
        raise HTTPException(409, "Discovery job evidence failed integrity")
    scope = Intake.model_validate(job.payload).evidence.model_dump(include=SCOPE_FIELDS)
    _check_legacy(db, **scope)
    return job_view(job)


class SourceSigningKey(BaseModel):
    model_config = ConfigDict(extra="forbid")
    public_key_hex: str = Field(pattern=r"^[0-9a-f]{64}$")
    previous_public_key_hex: str | None = Field(None, pattern=r"^[0-9a-f]{64}$")


@router.put("/intake/sources/{source_id}/signing-key", dependencies=owner)
def enroll_signing_key(source_id: str, request: SourceSigningKey, db: Session = Depends(get_db)):
    if not intake_ready(db):
        raise HTTPException(503, "Discovery intake not migrated")
    source = db.scalar(select(SourceRegistryItem).filter_by(source_id=source_id).with_for_update())
    if source is None or source.source_type.upper() not in {"DEMAND_EXPORT", "PROCUREMENT_EXPORT"}:
        raise HTTPException(404, "Eligible discovery source not found")
    proposed = f"ed25519:{request.public_key_hex}"
    if source.provenance_method == proposed:
        return {"source_id": source_id, "signature_required": True}
    current = source.provenance_method
    if current and current != f"ed25519:{request.previous_public_key_hex}":
        raise HTTPException(409, "Existing source provenance does not match the expected key")
    if not current and request.previous_public_key_hex:
        raise HTTPException(409, "Prior source signing key not found")
    source.provenance_method = proposed
    db.commit()
    return {"source_id": source_id, "signature_required": True}
