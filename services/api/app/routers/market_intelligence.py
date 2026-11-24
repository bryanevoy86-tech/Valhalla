"""Owner-private investment research and paper FX. No broker or payment boundary."""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.market_intelligence import MarketEvidence
from app.schemas.market_intelligence import FXBatch, FXReplay, InvestmentReplay, MarketEvidenceIn, SecurityBatch
from app.services.market_intelligence import (
    REPLAY_EVENT, check_replay_event, checked_record, evidence_digest, market_schema, replay_event_id, require_source, source_detail,
)
from app.services.market_replay import fx_replay, investment_replay, research_snapshot
from app.services.prime_business_execution import _check_legacy, _emergency_stop_active, _event, require_owner_mandate_key
from app.services.specialist_triggers import outcome_scope_key


def require_schema(db: Session = Depends(get_db)):
    if not market_schema(db):
        raise HTTPException(503, "Market intelligence schema unavailable")


router = APIRouter(prefix="/api/prime/market", tags=["market-intelligence"],
                   dependencies=[Depends(require_prime_control_key), Depends(require_schema)])
owner = [Depends(require_owner_mandate_key)]


def now():
    return datetime.now(timezone.utc)


def get_evidence(db, evidence_id, *, lock=False):
    row = db.get(MarketEvidence, evidence_id, with_for_update=lock, populate_existing=lock)
    if row is None:
        raise HTTPException(404, "Market evidence not found")
    return row


@router.post("/evidence", status_code=201, dependencies=owner)
def ingest(request: MarketEvidenceIn, db: Session = Depends(get_db)):
    scope = request.scope.model_dump()
    _check_legacy(db, **scope)
    received = now()
    data = request.data
    if isinstance(data, SecurityBatch):
        observed = [data.bars[-1].at]
        if data.fundamentals:
            observed.append(data.fundamentals.available_at)
    elif isinstance(data, FXBatch):
        observed = [quote.at for quote in data.quotes]
    else:
        observed = [data.published_at]
    if max(observed) > received:
        raise HTTPException(422, "Observations cannot be in the future")
    require_source(db, request, lock=True)
    payload = request.model_dump(mode="json")
    digest = evidence_digest(payload, request.evidence_id)
    row = db.get(MarketEvidence, request.evidence_id)
    if row:
        if row.digest != digest or row.digest != evidence_digest(row.payload, row.id):
            raise HTTPException(409, "Market evidence ID already used")
    else:
        row = MarketEvidence(id=request.evidence_id, scope_key=outcome_scope_key(scope),
                             kind=data.kind, received_at=received, digest=digest, payload=payload)
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Market evidence ID already used") from None
    return {**source_detail(row, request), "revoked": row.revoked_at is not None}


@router.delete("/evidence/{evidence_id}", dependencies=owner)
def revoke(evidence_id: UUID, db: Session = Depends(get_db)):
    row = get_evidence(db, evidence_id, lock=True)
    if row.revoked_at is None:
        row.revoked_at = now()
        db.commit()
    return {"evidence_id": row.id, "revoked": True}


@router.get("/evidence/{evidence_id}/research")
def read_research(evidence_id: UUID, db: Session = Depends(get_db)):
    row = get_evidence(db, evidence_id)
    scope = row.payload.get("scope", {}) if isinstance(row.payload, dict) else {}
    record = checked_record(db, row, scope)
    _check_legacy(db, **scope)
    data = record.data
    detail = data.model_dump(mode="json")
    if isinstance(data, SecurityBatch):
        detail = research_snapshot(data, now())
    return {"source": source_detail(row, record), "research": detail, "authority": "ADVISOR_ONLY"}


def load_replay(db, run_id):
    return db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=replay_event_id(run_id), event_type=REPLAY_EVENT))


def run_replay(request, db, kind):
    scope = request.scope.model_dump()
    _check_legacy(db, **scope)
    if _emergency_stop_active(db):
        raise HTTPException(503, "Market replay paused by emergency stop")
    if request.as_of > now():
        raise HTTPException(422, "Replay cutoff cannot be in the future")
    params = request.model_dump(mode="json")
    event = load_replay(db, request.run_id)
    if event is not None:
        receipt = check_replay_event(event)
        if receipt["request"] != params or receipt["kind"] != kind:
            raise HTTPException(409, "Market replay ID already used")
    ids = [request.dataset_id] if kind == "FX" else [*(item.dataset_id for item in request.portfolio), request.benchmark_id]
    records = {}
    for evidence_id in sorted(set(ids)):
        row = get_evidence(db, evidence_id)
        records[evidence_id] = checked_record(db, row, scope)
    for record in sorted(records.values(), key=lambda item: item.source_id):
        require_source(db, record, lock=True)
    for evidence_id, prior in records.items():
        row = get_evidence(db, evidence_id, lock=True)
        record = checked_record(db, row, scope)
        if record != prior:
            raise HTTPException(409, "Market evidence changed during replay")
        records[evidence_id] = (row, record)
    provenance = [source_detail(*records[evidence_id]) for evidence_id in ids]
    if event is not None:
        if receipt["sources"] != provenance:
            raise HTTPException(409, "Market replay provenance changed")
        return receipt
    datasets = [records[evidence_id][1].data for evidence_id in ids]
    try:
        if kind == "FX" and isinstance(datasets[0], FXBatch):
            result = fx_replay(request, datasets[0])
        elif kind == "INVESTMENT" and all(isinstance(dataset, SecurityBatch) for dataset in datasets):
            result = investment_replay(request, datasets[:-1], datasets[-1])
        else:
            raise ValueError("Market evidence kind does not match the requested replay")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    receipt = {"run_id": str(request.run_id), "kind": kind, "scope": scope, "request": params, "sources": provenance,
               "recorded_at": now().isoformat(), "result": result, "engine_version": 1,
               "basis": "HISTORICAL_PAPER_SIMULATION", "authority": "ADVISOR_ONLY",
               "external_execution_authorized": False, "verified_real_world_outcome": False}
    event_id = replay_event_id(request.run_id)
    receipt["receipt_sha256"] = artifact_digest("market_paper_replay", event_id, receipt)
    _event(db, event_id=event_id, legacy_instance_id=scope["legacy_instance_id"], event_type=REPLAY_EVENT,
           message="Internal deterministic market replay recorded", payload=receipt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Market replay ID already used") from None
    return receipt


@router.post("/replays/investment", status_code=201, dependencies=owner)
def replay_investment(request: InvestmentReplay, db: Session = Depends(get_db)):
    return run_replay(request, db, "INVESTMENT")


@router.post("/replays/fx", status_code=201, dependencies=owner)
def replay_fx(request: FXReplay, db: Session = Depends(get_db)):
    return run_replay(request, db, "FX")


@router.get("/replays/{run_id}")
def read_replay(run_id: UUID, db: Session = Depends(get_db)):
    event = load_replay(db, run_id)
    if event is None:
        raise HTTPException(404, "Market replay not found")
    receipt = check_replay_event(event)
    _check_legacy(db, **receipt["scope"])
    return receipt
