"""Prospective source-pinned market forecasts for the private Norns lane."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.models.market_intelligence import MarketEvidence
from app.models.norns_forecast import NornsMarketForecast
from app.schemas.market_intelligence import MarketForecastIn, MarketForecastResolution, MarketScope, SecurityBatch
from app.services.market_intelligence import authorized_source, checked_record, market_schema, source_detail
from app.services.prime_business_execution import _check_legacy, _emergency_stop_active, require_owner_mandate_key
from app.services.specialist_triggers import outcome_scope_key


def now():
    return datetime.now(timezone.utc)


def utc(at):
    return at if at.tzinfo else at.replace(tzinfo=timezone.utc)


def require_schema(db: Session = Depends(get_db)):
    if not market_schema(db) or not inspect(db.connection()).has_table(NornsMarketForecast.__tablename__):
        raise HTTPException(503, "Norns market forecast schema unavailable")


router = APIRouter(prefix="/api/prime/norns/market", tags=["norns"],
                   dependencies=[Depends(require_prime_control_key), Depends(require_schema)])
owner = [Depends(require_owner_mandate_key)]


def _read(row):
    if row.digest != artifact_digest("norns_market_forecast", str(row.id), row.payload):
        raise HTTPException(409, "Market forecast integrity check failed")
    request = MarketForecastIn.model_validate(row.payload["request"])
    if (request.forecast_id != row.id or request.probability_bp != row.probability_bp
            or outcome_scope_key(request.scope.model_dump()) != row.scope_key
            or datetime.fromisoformat(row.payload["issued_at"]) != utc(row.issued_at)
            or row.payload["baseline"]["evidence_class"] != row.evidence_class):
        raise HTTPException(409, "Market forecast metadata changed")
    if row.settlement:
        settlement = {key: value for key, value in row.settlement.items() if key != "sha256"}
        if (row.observed_outcome != settlement.get("observed_outcome")
                or row.settlement.get("sha256") != artifact_digest("norns_market_resolution", row.digest, settlement)):
            raise HTTPException(409, "Market forecast settlement integrity check failed")
    elif row.observed_outcome is not None:
        raise HTTPException(409, "Market forecast settlement is missing")
    return request


def _view(row):
    _read(row)
    return {**row.payload, "sha256": row.digest, "settlement": row.settlement,
            "estimate_source": "OWNER_PROBABILITY", "target": "SECURITY_UTC_DAILY_CLOSE_ABOVE_THRESHOLD",
            "independent_market_truth_verified": False}


def _commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A forecast for this scoped market target already exists") from None


@router.post("/forecasts", status_code=201, dependencies=owner)
def create_forecast(request: MarketForecastIn, db: Session = Depends(get_db)):
    scope = request.scope.model_dump()
    _check_legacy(db, **scope)
    params = request.model_dump(mode="json")
    existing = db.get(NornsMarketForecast, request.forecast_id)
    if existing:
        if existing.payload["request"] != params:
            raise HTTPException(409, "Forecast ID already used")
        return _view(existing)
    if _emergency_stop_active(db):
        raise HTTPException(503, "Market forecast intake paused")
    issued = now()
    if not issued.date() < request.target_date <= issued.date() + timedelta(days=30):
        raise HTTPException(422, "Target date must be a future UTC date within 30 days")
    row = db.get(MarketEvidence, request.baseline_evidence_id, with_for_update=True)
    if row is None:
        raise HTTPException(404, "Baseline evidence not found")
    baseline = checked_record(db, row, scope)
    data = baseline.data
    if (not isinstance(data, SecurityBatch) or utc(row.received_at) > issued or data.bars[-1].at > issued
            or baseline.source_id == request.outcome_source_id):
        raise HTTPException(409, "Baseline requires an earlier security observation and a distinct outcome source")
    outcome_source = authorized_source(db, request.outcome_source_id, request.scope.jurisdiction, baseline.evidence_class)
    if baseline.evidence_class == "SIMULATION" and outcome_source.data_class not in {"sandbox", "test", "synthetic"}:
        raise HTTPException(409, "Simulation forecasts require a separately registered simulation outcome source")
    payload = {"request": params, "baseline": source_detail(row, baseline), "symbol": data.symbol,
               "asset_class": data.asset_class, "currency": data.currency, "issued_at": issued.isoformat()}
    scope_key = outcome_scope_key(scope)
    target_key = artifact_digest("norns_market_target", scope_key, {
        "symbol": data.symbol, "currency": data.currency, "target_date": request.target_date.isoformat(),
        "evidence_class": baseline.evidence_class,
    })
    forecast = NornsMarketForecast(id=request.forecast_id, scope_key=scope_key, target_key=target_key,
                                    evidence_class=baseline.evidence_class, probability_bp=request.probability_bp,
                                    issued_at=issued, payload=payload,
                                    digest=artifact_digest("norns_market_forecast", str(request.forecast_id), payload))
    db.add(forecast)
    _commit(db)
    return _view(forecast)


@router.get("/forecasts/{forecast_id}")
def read_forecast(forecast_id: UUID, db: Session = Depends(get_db)):
    row = db.get(NornsMarketForecast, forecast_id)
    if row is None:
        raise HTTPException(404, "Market forecast not found")
    request = _read(row)
    _check_legacy(db, **request.scope.model_dump())
    return _view(row)


@router.post("/forecasts/{forecast_id}/resolve", dependencies=owner)
def resolve_forecast(forecast_id: UUID, resolution: MarketForecastResolution, db: Session = Depends(get_db)):
    forecast = db.get(NornsMarketForecast, forecast_id, with_for_update=True)
    if forecast is None:
        raise HTTPException(404, "Market forecast not found")
    request = _read(forecast)
    scope = request.scope.model_dump()
    _check_legacy(db, **scope)
    if forecast.settlement:
        if forecast.settlement["outcome_source"]["id"] != str(resolution.outcome_evidence_id):
            raise HTTPException(409, "Forecast already resolved with different evidence")
        return _view(forecast)
    current = now()
    if current.date() <= request.target_date:
        raise HTTPException(409, "The target UTC observation date has not closed")
    authorized_source(db, request.outcome_source_id, request.scope.jurisdiction, forecast.evidence_class, lock=True)
    rows = db.scalars(select(MarketEvidence).where(
        MarketEvidence.scope_key == forecast.scope_key, MarketEvidence.kind == "SECURITY",
        MarketEvidence.revoked_at.is_(None),
        MarketEvidence.payload["source_id"].as_string() == request.outcome_source_id,
        MarketEvidence.payload["data"]["symbol"].as_string() == forecast.payload["symbol"],
        MarketEvidence.received_at > forecast.issued_at,
    ).order_by(MarketEvidence.id).limit(101).with_for_update()).all()
    if len(rows) > 100:
        raise HTTPException(409, "Too many competing observations to resolve automatically")
    observations = {}
    for row in rows:
        record = checked_record(db, row, scope)
        data = record.data
        if (record.evidence_class == forecast.evidence_class and data.currency == forecast.payload["currency"]
                and data.asset_class == forecast.payload["asset_class"] and utc(row.received_at) <= current):
            for bar in data.bars:
                if bar.at.date() == request.target_date and utc(forecast.issued_at) < bar.at <= current:
                    observations[row.id] = (bar, source_detail(row, record))
    if resolution.outcome_evidence_id not in observations:
        raise HTTPException(409, "No eligible close from the pinned independent outcome source")
    bar, evidence = observations[resolution.outcome_evidence_id]
    if any(other.close != bar.close or other.at != bar.at for other, _ in observations.values()):
        raise HTTPException(409, "Conflicting close observations require evidence reconsideration")
    outcome = int(bar.close > request.threshold_close)
    settlement = {"observed_outcome": outcome, "observed_close": str(bar.close),
                  "outcome_at": bar.at.isoformat(), "outcome_source": evidence, "resolved_at": current.isoformat()}
    forecast.observed_outcome = outcome
    forecast.settlement = {**settlement, "sha256": artifact_digest("norns_market_resolution", forecast.digest, settlement)}
    _commit(db)
    return _view(forecast)


@router.post("/calibration")
def calibration(scope: MarketScope, evidence_class: Literal["SIMULATION", "OPERATOR_REPORTED"],
                cohort: Literal["PROSPECTIVE", "HOLDOUT"], db: Session = Depends(get_db)):
    values = scope.model_dump()
    _check_legacy(db, **values)
    rows = db.scalars(select(NornsMarketForecast).where(
        NornsMarketForecast.scope_key == outcome_scope_key(values), NornsMarketForecast.evidence_class == evidence_class,
        NornsMarketForecast.observed_outcome.is_not(None),
        NornsMarketForecast.payload["request"]["cohort"].as_string() == cohort,
    ).order_by(NornsMarketForecast.issued_at.desc(), NornsMarketForecast.id).limit(200)).all()
    squared_errors = []
    excluded = 0
    for row in rows:
        _read(row)
        try:
            for expected in (row.payload["baseline"], row.settlement["outcome_source"]):
                evidence = db.get(MarketEvidence, UUID(expected["id"]))
                if evidence is None or evidence.digest != expected["sha256"]:
                    raise HTTPException(409, "Calibration source evidence changed")
                checked_record(db, evidence, values)
        except HTTPException:
            excluded += 1
            continue
        squared_errors.append((row.probability_bp - 10000 * row.observed_outcome) ** 2)
    count = len(squared_errors)
    return {"cohort": cohort, "evidence_class": evidence_class, "resolved_sample_count": count,
            "excluded_sample_count": excluded, "sample_limit": 200,
            "brier_score": round(Decimal(sum(squared_errors)) / (100_000_000 * count), 6) if count else None,
            "independent_market_truth_verified": False}
