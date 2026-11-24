"""Scope-bound mandate reviews and internal economic decision rehearsal."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.loki.models import LokiReview
from app.loki.review_service import reviewer_identity, verdict
from app.models.economic_control import EconomicOperation, EconomicPool, EconomicRecord
from app.schemas.economic_control import AssetRecovery, Containment, Decision, Liquidity, Mandate, MarketScope, Obligation, Opportunity, Performance, Plan, ReservationRelease
from app.services.economic_control import (
    ADVICE_TYPE, CONTAINMENT, assessment, business_contained, current_performance, load_state, lock_capital_pools,
    lock_pool, operation_key, pool_liquidity, ready,
    store_record, trigger_reassessment, verified_payload, verify_checkout_performance,
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


def context(db, scope, *, lock=True, new_currency=None, lock_all_pools=False):
    values = scope.model_dump()
    _check_legacy(db, **values)
    key = operation_key(values)
    operation = db.get(EconomicOperation, key)
    currency = operation.currency if operation else new_currency
    if currency is None:
        raise HTTPException(404, "Economic operation is not enrolled")
    if lock_all_pools:
        pool = lock_capital_pools(db).get(currency)
    else:
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


def record_payload(request):
    return request.journal_payload() if isinstance(request, Performance) else request.model_dump(mode="json")


def existing_record(db, operation, kind, request):
    row = db.get(EconomicRecord, request.id)
    if row is None:
        return None
    previous = verified_payload(row)
    expected = previous["request"] if kind == "DECISION" and row.kind == "DECISION" else previous
    if row.kind != kind or row.scope_key != operation.scope_key or expected != record_payload(request):
        raise HTTPException(409, "Economic record ID already used")
    return row


def store(db, operation, kind, request, *, receipt_ref=None, durable=True):
    row = store_record(db, operation, kind, record_payload(request), receipt_ref=receipt_ref)
    trigger_reassessment(db, operation.scope, row.id, now().replace(tzinfo=None))
    commit(db) if durable else db.flush()
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
    operation, state, pool = context(db, request.scope, new_currency=request.currency, lock_all_pools=True)
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
    if not previous and request.opening_additional_funding:
        if _emergency_stop_active(db) or business_contained(db, operation.scope, exclude_scope_key=operation.scope_key):
            raise HTTPException(409, "Economic containment or emergency stop blocks opening commitments")
    if not previous:
        pool.committed_minor += request.opening_additional_funding
    return store(db, operation, "MANDATE", request, receipt_ref=request.opening_receipt_ref)


@router.post("/performance", status_code=201, dependencies=owner)
def performance(request: Performance, db: Session = Depends(get_db)):
    return _performance(request, db)


def _performance(request: Performance, db: Session, *, durable=True):
    # Match delivery's order-before-pool lock order.
    checkout = verify_checkout_performance(db, request, lock=True)
    operation, state, pool = context(db, request.scope)
    if checkout is not None and checkout["currency"] != pool.currency:
        raise HTTPException(409, "Checkout currency differs from the economic operation")
    row = existing_record(db, operation, "PERFORMANCE", request)
    if row:
        return retry(row)
    if request.end > now().date() or (state.performance and request.start != state.performance.end + timedelta(days=1)):
        raise HTTPException(409, "Performance evidence must be chronological and gap-free")
    return store(db, operation, "PERFORMANCE", request, receipt_ref=request.receipt_ref, durable=durable)


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


@router.post("/obligations", status_code=201, dependencies=owner)
def obligation(request: Obligation, db: Session = Depends(get_db)):
    operation, state, _ = context(db, request.scope)
    row = existing_record(db, operation, "OBLIGATION", request)
    if row:
        return retry(row)
    previous = state.obligations.get(request.obligation_key)
    if request.previous_id != (previous.id if previous else None):
        raise HTTPException(409, "Obligation revision must bind the current record")
    if not previous and request.status == "CLOSED_IN_FIXTURE":
        raise HTTPException(409, "A closed obligation requires a prior record")
    return store(db, operation, "OBLIGATION", request, receipt_ref=request.evidence_ref)


@router.post("/reservation-releases", status_code=201, dependencies=owner)
def release_reservation(request: ReservationRelease, db: Session = Depends(get_db)):
    operation, state, pool = context(db, request.scope)
    current = db.get(EconomicRecord, request.id)
    body = request.model_dump(mode="json")
    if current:
        payload = verified_payload(current)
        if current.scope_key != operation.scope_key or current.kind != "RELEASE" or any(
            payload.get(key) != value for key, value in body.items()
        ):
            raise HTTPException(409, "Release identity already used")
        return {**payload, "sha256": current.digest}
    amount = state.active_reservations.get(request.decision_id)
    if not amount or pool.committed_minor < amount:
        raise HTTPException(409, "No releasable reservation exists in this scope")
    payload = {**body, "released_simulation_minor": amount, "external_authority": False,
               "cumulative_budget_restored": False}
    pool.committed_minor -= amount
    row = store_record(db, operation, "RELEASE", payload, receipt_ref=request.evidence_ref)
    trigger_reassessment(db, operation.scope, request.id, now().replace(tzinfo=None))
    commit(db)
    return {**payload, "sha256": row.digest}


@router.post("/asset-recovery-fixtures", status_code=201, dependencies=owner)
def record_asset_recovery(request: AssetRecovery, db: Session = Depends(get_db)):
    from app.models.treasury_reconciliation import StatementImport
    from app.services.treasury_reconciliation import payload_for, statement_ready

    operation, state, _ = context(db, request.scope)
    document = request.model_dump(mode="json")
    current = db.get(EconomicRecord, request.id)
    if current:
        previous = verified_payload(current)
        if current.scope_key != operation.scope_key or current.kind != "RECOVERY" or previous.get("request") != document:
            raise HTTPException(409, "Recovery identity already used")
        return previous
    if any(item["request"]["exit_decision_id"] == str(request.exit_decision_id)
           and item["request"]["asset_ref"] == request.asset_ref for item in state.recoveries):
        raise HTTPException(409, "Asset already has a recovery fixture under this exit decision")
    if not statement_ready(db):
        raise HTTPException(503, "Statement fixture schema unavailable")
    exit_decision = db.get(EconomicRecord, request.exit_decision_id)
    statement = db.get(StatementImport, request.statement_id)
    if exit_decision is None or exit_decision.kind != "DECISION" or exit_decision.scope_key != operation.scope_key or statement is None:
        raise HTTPException(409, "Scoped exit decision and statement fixture are required")
    prior = verified_payload(exit_decision)
    asset = next((item for item in prior["asset_inventory"] if item["asset_ref"] == request.asset_ref), None)
    document_source = payload_for(statement)
    if prior["action"] != "EXIT" or not asset or document_source.scope.model_dump() != operation.scope or (
        document_source.currency != operation.currency or document_source.purpose != "BUSINESS"
    ):
        raise HTTPException(409, "Recovery scope or asset evidence does not match the exit")
    entry = next((item for item in document_source.entries if item.external_ref.casefold() == request.entry_ref.casefold()), None)
    if (entry is None or entry.category != "ASSET_RECOVERY" or entry.amount_minor <= 0
            or entry.posted_on < datetime.fromisoformat(prior["recorded_at"]).date()):
        raise HTTPException(409, "Recovery requires a positive classified fixture posting after the exit decision")
    payload = {"id": str(request.id), "scope": operation.scope, "request": document,
               "projected_liquidation_minor": asset["projected_liquidation_minor"],
               "observed_statement_fixture_minor": entry.amount_minor, "statement_sha256": statement.digest,
               "actual_recovered_capital_minor": None, "external_authority": False}
    receipt_key = f"recovery-fixture:{request.statement_id}:{entry.external_ref.casefold()}"
    store_record(db, operation, "RECOVERY", payload, receipt_ref=receipt_key)
    trigger_reassessment(db, operation.scope, request.id, now().replace(tzinfo=None))
    commit(db)
    return payload


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


@router.get("/portfolio-exposure", dependencies=owner)
def portfolio_exposure(db: Session = Depends(get_db)):
    current = now().date()
    pools = db.scalars(select(EconomicPool).order_by(EconomicPool.currency)).all()
    operations = db.scalars(select(EconomicOperation).order_by(EconomicOperation.scope_key)).all()
    totals = []
    for pool in pools:
        scoped = [load_state(db, operation) for operation in operations if operation.currency == pool.currency]
        reservations = sum(state.outstanding_reservations for state in scoped)
        if reservations != pool.committed_minor:
            raise HTTPException(409, "Aggregate reservation counter does not reconcile")
        recorded_exposure = sum(state.performance.outstanding_exposure for state in scoped
                                if current_performance(state, current))
        unknown = sum(not current_performance(state, current) for state in scoped)
        liquidity = pool_liquidity(db, pool)
        totals.append({
            "currency": pool.currency, "enrolled_operations": len(scoped),
            "outstanding_reservations_minor": reservations, "fresh_recorded_exposure_minor": recorded_exposure,
            "operations_without_fresh_exposure": unknown,
            "protected_liquidity_fixture_minor": liquidity.protected_pool_minor if liquidity else None,
            "liquidity_conflict": pool.liquidity_conflict,
        })
    return {"basis": "RECONCILIATION_FIXTURE", "totals": totals,
            "actual_organization_exposure_minor": None, "external_authority": False}


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
    operation, state, pool = context(db, plan.scope, lock_all_pools=True)
    row = existing_record(db, operation, "DECISION", plan)
    if row:
        record = verified_payload(row)
        if (record["independent_review_id"] != str(request.independent_review_id)
                or record["artifact_sha256"] != request.expected_artifact_sha256):
            raise HTTPException(409, "Economic decision replay differs from the recorded review")
        return record
    if _emergency_stop_active(db) and plan.action not in CONTAINMENT:
        raise HTTPException(503, "Economic rehearsal paused by emergency stop")
    snapshot = prepare(db, operation, state, pool, plan, lock_sources=True)
    digest = snapshot["artifact_sha256"]
    if request.expected_artifact_sha256 != digest:
        raise HTTPException(409, "Economic evidence changed and requires a new exact review")
    blockers = snapshot["raw_input"]["analysis"]["blockers"]
    if plan.cross_business_support or (blockers and plan.action not in CONTAINMENT):
        raise HTTPException(409, {"message": "Economic limits block this rehearsal", "blockers": blockers})
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
