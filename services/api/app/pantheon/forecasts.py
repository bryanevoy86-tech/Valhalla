"""Issue prospective, scope-specific baseline estimates from observed receipts."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models.completion_registry import LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.norns_forecast import NornsForecast, NornsHoldout
from app.services.prime_business_execution import ACTION_TYPE, _json, _receipt_id, action_status


SOURCE = "SCOPED_HISTORICAL_RATE"


def outcome_matches_receipt(db: Session, forecast, work, now) -> bool:
    """Recompute an internal deadline result from current Factory receipts."""
    if (work is None or _json(work.payload_json, {}).get("action_type") != ACTION_TYPE
            or forecast.observed_outcome not in (0, 1) or forecast.resolved_at is None
            or not forecast.issued_at < forecast.deadline_at
            or not forecast.issued_at <= forecast.resolved_at <= now):
        return False
    evidence_id = _receipt_id(forecast.action_id)
    negative_id = f"FACTORY_DEADLINE_NO_RECEIPT:{forecast.action_id}"
    if forecast.evidence_ref not in {evidence_id, negative_id}:
        return False
    if forecast.evidence_ref == negative_id and (
        forecast.observed_outcome != 0 or forecast.resolved_at < forecast.deadline_at
    ):
        return False

    result = action_status(db, forecast.action_id)
    if not result["internal_artifact_verified"]:
        return forecast.evidence_ref == negative_id and work.status != "completed" and db.scalar(
            select(LegacyOrchestrationEvent.id).where(LegacyOrchestrationEvent.event_id == evidence_id)
        ) is None
    try:
        verified_at = datetime.fromisoformat(result["receipt"]["verified_at"])
        if verified_at.tzinfo is None:
            return False
        verified_at = verified_at.astimezone(timezone.utc).replace(tzinfo=None)
    except (KeyError, TypeError, ValueError):
        return False
    if not forecast.issued_at <= verified_at <= now:
        return False
    if forecast.evidence_ref == negative_id:
        # A legitimate completion that arrived after the negative was recorded does not rewrite history.
        return verified_at > forecast.resolved_at
    return verified_at <= forecast.resolved_at and forecast.observed_outcome == int(verified_at <= forecast.deadline_at)


def calibration_measurements(db: Session, now, *, scope=None, estimate_source=None, cohort="ORDINARY") -> dict:
    forecast, work = NornsForecast, LegacyInstanceWorkItem
    holdout = exists(select(NornsHoldout.forecast_id).where(NornsHoldout.forecast_id == forecast.id))
    rows = select(forecast, work).outerjoin(work, work.action_id == forecast.action_id).where(
        forecast.observed_outcome.is_not(None), holdout if cohort == "HOLDOUT" else ~holdout,
    )
    if scope is not None:
        rows = rows.where(*(getattr(work, key) == value for key, value in scope.items()))
    if estimate_source is not None:
        rows = rows.where(forecast.estimate_source == estimate_source)
    count = excluded = squared_error = 0
    for estimate, action in db.execute(rows.execution_options(yield_per=100)):
        if not outcome_matches_receipt(db, estimate, action, now):
            excluded += 1
            continue
        count += 1
        squared_error += (estimate.probability_bp - 10000 * estimate.observed_outcome) ** 2
    return {"resolved_sample_count": count, "evidence_excluded_count": excluded,
            "brier_score": round(squared_error / count / 100_000_000, 6) if count else None}


def issue_scoped_estimate(db: Session, scope: dict, now, horizon_seconds: int) -> dict:
    work, forecast = LegacyInstanceWorkItem, NornsForecast
    filters = [getattr(work, key) == value for key, value in scope.items()]
    horizon = timedelta(seconds=horizon_seconds)
    history = db.execute(select(forecast, work).join(work, work.action_id == forecast.action_id).where(
        *filters, forecast.observed_outcome.is_not(None), forecast.resolved_at < now,
        ~exists(select(NornsHoldout.forecast_id).where(NornsHoldout.forecast_id == forecast.id)),
    ).order_by(forecast.resolved_at.desc(), forecast.id).limit(100)).all()
    sample = []
    for past, action in history:
        if past.deadline_at - past.issued_at != horizon or not outcome_matches_receipt(db, past, action, now):
            continue
        sample.append(past)
        if len(sample) == 30:
            break
    if len(sample) < 3:
        return {"forecast_status": "INSUFFICIENT_SCOPED_HISTORY", "training_count": len(sample)}

    candidate = db.scalar(select(work).where(
        *filters, work.status == "queued", work.action_id.like("bfd\\_%", escape="\\"),
        ~exists(select(forecast.id).where(forecast.action_id == work.action_id)),
        ~exists(select(LegacyOrchestrationEvent.id).where(
            LegacyOrchestrationEvent.event_id == "BF-RECEIPT-" + work.action_id,
        )),
    ).order_by(work.id).with_for_update(skip_locked=True).limit(1))
    if candidate is None or _json(candidate.payload_json, {}).get("action_type") != ACTION_TYPE:
        return {"forecast_status": "NO_NEW_FACTORY_ACTION", "training_count": len(sample)}

    probability_bp = round(10000 * (1 + sum(item.observed_outcome for item in sample)) / (2 + len(sample)))
    row = NornsForecast(
        id=uuid4(), action_id=candidate.action_id, probability_bp=probability_bp,
        issued_at=now, deadline_at=now + horizon, estimate_source=SOURCE,
        training_evidence={"eligible_forecast_ids": [str(item.id) for item in sample], "selection_cutoff": now.isoformat() + "Z"},
    )
    db.add(row)
    return {"forecast_status": "ISSUED", "forecast_id": str(row.id), "action_id": candidate.action_id,
            "estimate_source": SOURCE, "training_count": len(sample), "probability": probability_bp / 10000}
