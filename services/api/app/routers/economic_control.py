"""Scope-bound mandate reviews and internal economic decision rehearsal."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.loki.models import LokiReview
from app.loki.review_service import reviewer_identity, verdict
from app.models.economic_control import EconomicOperation, EconomicPool, EconomicRecord
from app.schemas.economic_control import Containment, Decision, Liquidity, Mandate, MarketScope, Opportunity, Performance, Plan
from app.services.economic_control import (
    ADVICE_TYPE, CONTAINMENT, assessment, load_state, lock_pool, operation_key, pool_liquidity, ready,
    store_record, trigger_reassessment, verified_payload,
)
from app.services.prime_business_execution import _check_legacy, _emergency_stop_active, require_owner_mandate_key


def now():
    return datetime.now(timezone.utc)


def require_schema(db: Session = Depends(get_db)):
    if not ready(db):
        raise HTTPException(503, "Economic control schema unavailable")


router = APIRouter(prefix="/api/prime/economy", tags=["economic-control"],
                   dependencies=[Depends(require_prime_control_key), Depends(require_schema)])
owner = [Depends(require_owner_mandate_key)]


def commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Economic identity, source receipt or sequence already used") from None


def context(db, scope, *, lock=True, new_currency=None):
    values = scope.model_dump()
    _check_legacy(db, **values)
    key = operation_key(values)
    operation = db.get(EconomicOperation, key)
    currency = operation.currency if operation else new_currency
    if currency is None:
        raise HTTPException(404, "Economic operation is not enrolled")
    pool = lock_pool(db, currency) if lock else db.get(EconomicPool, currency)
    if pool is None:
        raise HTTPException(503, "Economic currency pool unavailable")
    operation = db.get(EconomicOperation, key, populate_existing=True)
    if operation is None:
        if new_currency is None:
            raise HTTPException(404, "Economic operation is not enrolled")
        operation = EconomicOperation(scope_key=key, scope=values, currency=currency, sequence=0)
        db.add(operation)
    elif operation.scope != values or (new_currency is not None and operation.currency != new_currency):
        raise HTTPException(409, "An existing operation cannot reset its engine or currency")
    return operation, load_state(db, operation), pool


def existing_record(db, operation, kind, request):
    row = db.get(EconomicRecord, request.id)
    if row is None:
        return None
    previous = verified_payload(row)
    expected = previous["request"] if kind == "DECISION" and row.kind == "DECISION" else previous
    if row.kind != kind or row.scope_key != operation.scope_key or expected != request.model_dump(mode="json"):
        raise HTTPException(409, "Economic record ID already used")
    return row


def store(db, operation, kind, request, *, receipt_ref=None):
    row = store_record(db, operation, kind, request.model_dump(mode="json"), receipt_ref=receipt_ref)
    trigger_reassessment(db, operation.scope, row.id, now().replace(tzinfo=None))
    commit(db)
    return {"id": row.id, "sha256": row.digest, "sequence": row.sequence, "external_authority": False}


def retry(row):
    return {"id": row.id, "sha256": row.digest, "sequence": row.sequence, "external_authority": False}


@router.get("/historical-candidates")
def historical_candidates(db: Session = Depends(get_db)):
    from app.models.completion_registry import EngineRegistryItem
    from app.routers.completion_registry import PLANNED_ENGINE_CATALOG

    stored = {}
    if inspect(db.connection()).has_table(EngineRegistryItem.__tablename__):
        stored = {row.engine_id: row.current_state for row in db.scalars(select(EngineRegistryItem))}
    candidates = [
        {"engine_id": key, **details, "registry_state": stored.get(key), "requires_new_economic_review": True}
        for key, details in sorted(PLANNED_ENGINE_CATALOG.items())
    ]
    for key, title, category in (("storage_cleanouts", "Storage Cleanouts", "side_hustle"),
                                 ("landscaping", "Landscaping", "side_hustle")):
        if key not in PLANNED_ENGINE_CATALOG:
            candidates.append({"engine_id": key, "name": title, "category": category,
                               "business_industry": "local_services", "registry_state": stored.get(key),
                               "requires_new_economic_review": True})
    return {"candidates": candidates, "mandatory_startup_engines": [], "activation_authorized": False}


@router.post("/mandates", status_code=201, dependencies=owner)
def mandate(request: Mandate, db: Session = Depends(get_db)):
    operation, state, pool = context(db, request.scope, new_currency=request.currency)
    row = existing_record(db, operation, "MANDATE", request)
    if row:
        return retry(row)
    previous = state.mandate
    if request.review_by <= now().date():
        raise HTTPException(422, "Mandate review must be prospective")
    if request.previous_id != (previous.id if previous else None):
        raise HTTPException(409, "Mandate revision must bind the current version")
    if previous and (request.max_cumulative_loss > state.loss_limit
                     or request.max_additional_funding > state.funding_limit
                     or request.max_exposure > previous.max_exposure
                     or request.min_operating_reserve < previous.min_operating_reserve):
        raise HTTPException(409, "Ordinary mandate revisions cannot relax capital or reserve limits")
    if previous and (request.opening_cumulative_loss or request.opening_additional_funding or request.opening_receipt_ref):
        raise HTTPException(409, "A revision cannot restate opening accounting history")
    if not previous:
        pool.committed_minor += request.opening_additional_funding
    return store(db, operation, "MANDATE", request, receipt_ref=request.opening_receipt_ref)


@router.post("/performance", status_code=201, dependencies=owner)
def performance(request: Performance, db: Session = Depends(get_db)):
    operation, state, _ = context(db, request.scope)
    row = existing_record(db, operation, "PERFORMANCE", request)
    if row:
        return retry(row)
    if request.end > now().date() or (state.performance and request.start != state.performance.end + timedelta(days=1)):
        raise HTTPException(409, "Performance evidence must be chronological and gap-free")
    return store(db, operation, "PERFORMANCE", request, receipt_ref=request.receipt_ref)


@router.post("/liquidity", status_code=201, dependencies=owner)
def liquidity(request: Liquidity, db: Session = Depends(get_db)):
    operation, _, pool = context(db, request.scope)
    row = existing_record(db, operation, "LIQUIDITY", request)
    if row:
        return retry(row)
    previous = pool_liquidity(db, pool)
    if request.as_of > now().date() or (previous and request.as_of < previous.as_of):
        raise HTTPException(409, "Liquidity evidence must advance in time")
    if previous is None or request.as_of > previous.as_of:
        pool.liquidity_id = request.id
        pool.liquidity_conflict = False
    elif (request.unrestricted_pool_minor, request.protected_pool_minor) != (
        previous.unrestricted_pool_minor, previous.protected_pool_minor,
    ):
        pool.liquidity_conflict = True
    return store(db, operation, "LIQUIDITY", request, receipt_ref=request.receipt_ref)


@router.post("/containment", status_code=201, dependencies=owner)
def contain(request: Containment, db: Session = Depends(get_db)):
    operation, _, _ = context(db, request.scope)
    row = existing_record(db, operation, "CONTAINMENT", request)
    return retry(row) if row else store(db, operation, "CONTAINMENT", request)


@router.post("/opportunities", status_code=201, dependencies=owner)
def opportunity(request: Opportunity, db: Session = Depends(get_db)):
    operation, state, _ = context(db, request.scope)
    row = existing_record(db, operation, "OPPORTUNITY", request)
    if row:
        return retry(row)
    previous = state.opportunities.get(request.opportunity_key)
    if request.replaces_id != (previous.id if previous else None):
        raise HTTPException(409, "Opportunity revision must bind the current record")
    if len(state.opportunities) >= 40 and previous is None:
        raise HTTPException(409, "Scoped comparison is full")
    return store(db, operation, "OPPORTUNITY", request)


@router.post("/assessment")
def assess(scope: MarketScope, db: Session = Depends(get_db)):
    operation, state, pool = context(db, scope, lock=False)
    result = assessment(db, operation, state, pool, now().date())
    result["registry"] = [item.model_dump(mode="json") for item in state.opportunities.values()]
    return result


def prepare(db, operation, state, pool, plan, *, lock_sources=False):
    analysis = assessment(db, operation, state, pool, now().date(), plan, lock_sources=lock_sources)
    preview = {"plan": plan.model_dump(mode="json"), "analysis": analysis,
               "execution_authorized": False, "actual_recovered_capital_minor": None}
    digest = artifact_digest(ADVICE_TYPE, str(plan.id), preview)
    return {"artifact_type": ADVICE_TYPE, "input_source": "prime-economic-control",
            "heimdall_reference_id": str(plan.id), "artifact_sha256": digest, "raw_input": preview}


@router.post("/review-artifact")
def review_artifact(plan: Plan, db: Session = Depends(get_db)):
    operation, state, pool = context(db, plan.scope, lock=False)
    return prepare(db, operation, state, pool, plan)


@router.post("/decisions", status_code=201, dependencies=owner)
def record_decision(request: Decision, db: Session = Depends(get_db)):
    plan = request.plan
    operation, state, pool = context(db, plan.scope)
    row = existing_record(db, operation, "DECISION", plan)
    if row:
        record = verified_payload(row)
        if (record["independent_review_id"] != str(request.independent_review_id)
                or record["artifact_sha256"] != request.expected_artifact_sha256):
            raise HTTPException(409, "Economic decision replay differs from the recorded review")
        return record
    snapshot = prepare(db, operation, state, pool, plan, lock_sources=True)
    digest = snapshot["artifact_sha256"]
    if request.expected_artifact_sha256 != digest:
        raise HTTPException(409, "Economic evidence changed and requires a new exact review")
    blockers = snapshot["raw_input"]["analysis"]["blockers"]
    if plan.cross_business_support or (blockers and plan.action not in CONTAINMENT):
        raise HTTPException(409, {"message": "Economic limits block this rehearsal", "blockers": blockers})
    if _emergency_stop_active(db) and plan.action not in CONTAINMENT:
        raise HTTPException(503, "Economic rehearsal paused by emergency stop")
    reviewer_identity()
    if not inspect(db.connection()).has_table(LokiReview.__tablename__):
        raise HTTPException(503, "Independent review unavailable")
    review = db.get(LokiReview, request.independent_review_id, with_for_update=True)
    if (review is None or review.artifact_type != ADVICE_TYPE or review.heimdall_reference_id != str(plan.id)
            or review.artifact_sha256 != digest or not verdict(db, review).ok_to_proceed):
        raise HTTPException(409, "Exact independent Loki review and reconsideration are required")
    pool.committed_minor += plan.requested_additional_minor
    result = {"id": str(plan.id), "scope": operation.scope, "request": plan.model_dump(mode="json"),
              "action": plan.action, "reserved_simulation_minor": plan.requested_additional_minor,
              "reuse_candidates": [asset.model_dump(mode="json") for asset in plan.assets
                                   if asset.rights == "REUSE_PERMITTED" and not asset.obligations],
              "asset_inventory": [asset.model_dump(mode="json") for asset in plan.assets],
              "actual_recovered_capital_minor": None, "artifact_sha256": digest,
              "independent_review_id": str(review.id), "recorded_at": now().isoformat(),
              "observed": snapshot["raw_input"]["analysis"], "execution_authorized": False, "basis": "SIMULATION"}
    store_record(db, operation, "DECISION", result)
    trigger_reassessment(db, operation.scope, plan.id, now().replace(tzinfo=None))
    commit(db)
    return result


@router.get("/records/{record_id}")
def record(record_id: UUID, db: Session = Depends(get_db)):
    row = db.get(EconomicRecord, record_id)
    if row is None:
        raise HTTPException(404, "Economic record not found")
    payload = verified_payload(row)
    _check_legacy(db, **payload["scope"])
    return {"data": payload, "sha256": row.digest, "sequence": row.sequence, "external_authority": False}
