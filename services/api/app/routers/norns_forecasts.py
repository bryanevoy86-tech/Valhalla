"""Calibrate a bounded observable forecast against real internal Factory evidence."""
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.completion_registry import LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.norns_forecast import NornsForecast, NornsHoldout
from app.pantheon.forecasts import calibration_measurements, outcome_matches_receipt
from app.services.prime_business_execution import ACTION_TYPE, _json, _receipt_id, action_status, require_owner_mandate_key


def require_forecast_schema(db: Session = Depends(get_db)):
    schema = inspect(db.connection())
    if any(not schema.has_table(model.__tablename__) for model in (NornsForecast, NornsHoldout, LegacyInstanceWorkItem)):
        raise HTTPException(503, "Norns forecast schema not ready")


router = APIRouter(
    prefix="/api/prime/norns", tags=["norns"],
    dependencies=[Depends(require_prime_control_key), Depends(require_forecast_schema)],
)


class ForecastIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    forecast_id: UUID
    action_id: str = Field(pattern=r"^bfd_[0-9a-f]{32}$")
    probability_bp: int = Field(ge=0, le=10000, strict=True)
    horizon_seconds: int = Field(ge=30, le=2592000, strict=True)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _explain(forecast):
    return {
        "forecast_id": forecast.id, "action_id": forecast.action_id,
        "target": "VERIFIED_INTERNAL_ARTIFACT_BY_DEADLINE",
        "estimate_source": forecast.estimate_source, "probability": forecast.probability_bp / 10000,
        "training_evidence": forecast.training_evidence,
        "issued_at": forecast.issued_at.replace(tzinfo=timezone.utc),
        "deadline_at": forecast.deadline_at.replace(tzinfo=timezone.utc),
        "observed_outcome": forecast.observed_outcome, "evidence_ref": forecast.evidence_ref,
        "resolved_at": forecast.resolved_at.replace(tzinfo=timezone.utc) if forecast.resolved_at else None,
        "commercial_result": False,
    }


def _lock_work(db, action_id):
    item = db.scalar(select(LegacyInstanceWorkItem).where(
        LegacyInstanceWorkItem.action_id == action_id,
    ).with_for_update())
    if item is None or _json(item.payload_json, {}).get("action_type") != ACTION_TYPE:
        raise HTTPException(404, "Internal Factory action not found")
    return item


@router.post("/forecasts", status_code=201, dependencies=[Depends(require_owner_mandate_key)])
def create_forecast(payload: ForecastIn, db: Session = Depends(get_db)):
    item = _lock_work(db, payload.action_id)
    existing = db.get(NornsForecast, payload.forecast_id)
    if existing:
        if (existing.action_id != payload.action_id or existing.probability_bp != payload.probability_bp
                or existing.deadline_at - existing.issued_at != timedelta(seconds=payload.horizon_seconds)):
            raise HTTPException(409, "Forecast ID already used")
        return _explain(existing)
    if item.status != "queued":
        raise HTTPException(409, "A forecast must be recorded before execution")
    if db.scalar(select(LegacyOrchestrationEvent.id).where(
        LegacyOrchestrationEvent.event_id == _receipt_id(item.action_id),
    )) is not None:
        raise HTTPException(409, "An outcome receipt already exists")
    issued = _now()
    forecast = NornsForecast(
        id=payload.forecast_id, action_id=item.action_id, probability_bp=payload.probability_bp,
        issued_at=issued, deadline_at=issued + timedelta(seconds=payload.horizon_seconds),
    )
    db.add(forecast)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An immutable forecast already exists") from None
    return _explain(forecast)


@router.get("/forecasts/{forecast_id}")
def read_forecast(forecast_id: UUID, db: Session = Depends(get_db)):
    forecast = db.get(NornsForecast, forecast_id)
    if forecast is None:
        raise HTTPException(404, "Forecast not found")
    if forecast.resolved_at is not None:
        item = db.scalar(select(LegacyInstanceWorkItem).where(LegacyInstanceWorkItem.action_id == forecast.action_id))
        if not outcome_matches_receipt(db, forecast, item, _now()):
            raise HTTPException(409, "Recorded outcome no longer matches Factory evidence")
    return _explain(forecast)


@router.post("/forecasts/{forecast_id}/resolve")
def resolve_forecast(forecast_id: UUID, db: Session = Depends(get_db)):
    forecast = db.get(NornsForecast, forecast_id, with_for_update=True)
    if forecast is None:
        raise HTTPException(404, "Forecast not found")
    item = _lock_work(db, forecast.action_id)
    now = _now()
    if forecast.resolved_at is not None:
        if not outcome_matches_receipt(db, forecast, item, now):
            raise HTTPException(409, "Recorded outcome no longer matches Factory evidence")
        return _explain(forecast)
    result = action_status(db, forecast.action_id)
    if result["internal_artifact_verified"]:
        try:
            at = datetime.fromisoformat(result["receipt"]["verified_at"])
            if at.tzinfo is None:
                raise ValueError
            at = at.astimezone(timezone.utc).replace(tzinfo=None)
            if not forecast.issued_at <= at <= now:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise HTTPException(409, "Verified receipt timing is unavailable") from None
        forecast.observed_outcome = int(at <= forecast.deadline_at)
        forecast.evidence_ref = _receipt_id(forecast.action_id)
    elif item.status == "completed" or db.scalar(select(LegacyOrchestrationEvent.id).where(
        LegacyOrchestrationEvent.event_id == _receipt_id(forecast.action_id),
    )) is not None:
        raise HTTPException(409, "Existing Factory evidence is unverified")
    elif now >= forecast.deadline_at:
        forecast.observed_outcome = 0
        forecast.evidence_ref = f"FACTORY_DEADLINE_NO_RECEIPT:{forecast.action_id}"
    else:
        raise HTTPException(409, "Forecast remains pending")
    forecast.resolved_at = now
    db.commit()
    return _explain(forecast)


@router.post("/forecasts/{forecast_id}/holdout", status_code=201, dependencies=[Depends(require_owner_mandate_key)])
def enroll_holdout(forecast_id: UUID, db: Session = Depends(get_db)):
    forecast = db.get(NornsForecast, forecast_id, with_for_update=True)
    if forecast is None:
        raise HTTPException(404, "Forecast not found")
    existing = db.get(NornsHoldout, forecast.id)
    if existing is not None:
        return {"forecast_id": forecast.id, "cohort": "HOLDOUT", "enrolled_at": existing.enrolled_at}
    item = _lock_work(db, forecast.action_id)
    now = _now()
    if (forecast.observed_outcome is not None or not forecast.issued_at <= now < forecast.deadline_at
            or item.status != "queued" or db.scalar(select(LegacyOrchestrationEvent.id).where(
                LegacyOrchestrationEvent.event_id == _receipt_id(item.action_id),
            )) is not None):
        raise HTTPException(409, "Holdout enrollment must precede observable execution and deadline")
    row = NornsHoldout(forecast_id=forecast.id, enrolled_at=now)
    db.add(row)
    db.commit()
    return {"forecast_id": forecast.id, "cohort": "HOLDOUT", "enrolled_at": row.enrolled_at}


@router.get("/calibration")
def calibration(estimate_source: Literal["OWNER_ESTIMATE", "SCOPED_HISTORICAL_RATE"] = "OWNER_ESTIMATE",
                cohort: Literal["ORDINARY", "HOLDOUT"] = "ORDINARY",
                horizon_seconds: int | None = Query(None, ge=30, le=2592000), db: Session = Depends(get_db)):
    result = calibration_measurements(db, _now(), estimate_source=estimate_source, cohort=cohort,
                                      horizon_seconds=horizon_seconds)
    return {
        "target": "VERIFIED_INTERNAL_ARTIFACT_BY_DEADLINE", "estimate_source": estimate_source, "cohort": cohort,
        **result, "accuracy_claim": "OBSERVED_INTERNAL_SAMPLE" if result["resolved_sample_count"] else "INSUFFICIENT_EVIDENCE",
    }
