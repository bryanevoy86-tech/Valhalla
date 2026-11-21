"""Issue prospective, scope-specific baseline estimates from observed receipts."""
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from app.models.completion_registry import LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.norns_forecast import NornsForecast, NornsHoldout
from app.services.prime_business_execution import ACTION_TYPE, _json, _receipt_id, action_status


SOURCE = "SCOPED_HISTORICAL_RATE"


def resolve_factory_outcome(db: Session, forecast, item, now) -> None:
    """Label an unresolved forecast with the forecast and work rows locked."""
    if not forecast.issued_at <= now or not forecast.issued_at < forecast.deadline_at:
        raise HTTPException(409, "Forecast timing is invalid")
    payload = _json(item.payload_json, {})
    if not isinstance(payload, dict) or payload.get("action_type") != ACTION_TYPE:
        raise HTTPException(409, "Internal Factory action evidence is unverified")
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


def sweep_scoped_outcomes(db: Session, scope: dict, now, *, after: UUID | None = None) -> dict:
    """Review one page in the existing Norns assignment transaction."""
    forecast, work = NornsForecast, LegacyInstanceWorkItem
    window = 20
    receipt = exists(select(LegacyOrchestrationEvent.id).where(
        LegacyOrchestrationEvent.event_id == "BF-RECEIPT-" + forecast.action_id,
    ))
    query = select(forecast.id).join(work, work.action_id == forecast.action_id).where(
        *(getattr(work, key) == value for key, value in scope.items()),
        forecast.resolved_at.is_(None),
        or_(forecast.deadline_at <= now, receipt, work.status == "completed"),
    )
    if after is not None:
        query = query.where(forecast.id > after)
    ids = db.scalars(query.order_by(forecast.id).limit(window + 1)).all()
    findings = {"resolved_ids": [], "unverified_ids": [], "deferred_count": 0,
                "next_after": str(ids[window - 1]) if len(ids) > window else None}
    for forecast_id in ids[:window]:
        estimate = db.scalar(select(forecast).filter_by(id=forecast_id, resolved_at=None)
                             .with_for_update(skip_locked=True))
        if estimate is None:
            findings["deferred_count"] += 1
            continue
        item = db.scalar(select(work).filter_by(action_id=estimate.action_id, **scope)
                         .with_for_update(skip_locked=True))
        if item is None:
            findings["deferred_count"] += 1
            continue
        try:
            resolve_factory_outcome(db, estimate, item, now)
        except HTTPException as exc:
            if exc.status_code != 409:
                raise
            findings["unverified_ids"].append(str(forecast_id))
        else:
            findings["resolved_ids"].append(str(forecast_id))
    db.flush()
    return findings


def outcome_matches_receipt(db: Session, forecast, work, now, *, enrolled_at=None) -> bool:
    """Recompute an internal deadline result from current Factory receipts."""
    if (work is None or _json(work.payload_json, {}).get("action_type") != ACTION_TYPE
            or forecast.observed_outcome not in (0, 1) or forecast.resolved_at is None
            or not forecast.issued_at < forecast.deadline_at
            or not forecast.issued_at <= forecast.resolved_at <= now):
        return False
    if enrolled_at is not None and not forecast.issued_at <= enrolled_at < min(
        forecast.deadline_at, forecast.resolved_at
    ):
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
    if not forecast.issued_at <= verified_at <= now or (enrolled_at is not None and verified_at <= enrolled_at):
        return False
    if forecast.evidence_ref == negative_id:
        # A legitimate completion that arrived after the negative was recorded does not rewrite history.
        return verified_at > forecast.resolved_at
    return verified_at <= forecast.resolved_at and forecast.observed_outcome == int(verified_at <= forecast.deadline_at)


def calibration_measurements(
    db: Session, now, *, scope=None, estimate_source=None, cohort="ORDINARY", horizon_seconds=None,
) -> dict:
    forecast, work = NornsForecast, LegacyInstanceWorkItem
    holdout = NornsHoldout
    rows = select(forecast, work, holdout.enrolled_at).outerjoin(
        work, work.action_id == forecast.action_id,
    ).outerjoin(
        holdout, holdout.forecast_id == forecast.id,
    ).where(
        forecast.observed_outcome.is_not(None),
        holdout.forecast_id.is_not(None) if cohort == "HOLDOUT" else holdout.forecast_id.is_(None),
    )
    if scope is not None:
        rows = rows.where(*(getattr(work, key) == value for key, value in scope.items()))
    if estimate_source is not None:
        rows = rows.where(forecast.estimate_source == estimate_source)
    horizon = timedelta(seconds=horizon_seconds) if horizon_seconds is not None else None
    buckets = [[0, 0, 0] for _ in range(10)]
    count = excluded = squared_error = 0
    for estimate, action, enrollment in db.execute(rows.execution_options(yield_per=100)):
        if horizon is not None and estimate.deadline_at - estimate.issued_at != horizon:
            continue
        if not outcome_matches_receipt(db, estimate, action, now, enrolled_at=enrollment):
            excluded += 1
            continue
        count += 1
        probability = estimate.probability_bp
        outcome = estimate.observed_outcome
        squared_error += (probability - 10000 * outcome) ** 2
        bucket = buckets[min(probability // 1000, 9)]
        bucket[0] += 1
        bucket[1] += probability
        bucket[2] += outcome
    return {
        "horizon_seconds": horizon_seconds,
        "resolved_sample_count": count,
        "evidence_excluded_count": excluded,
        "brier_score": round(squared_error / count / 100_000_000, 6) if count else None,
        "probability_buckets": [
            {
                "lower_bp": index * 1000,
                "upper_bp": (index + 1) * 1000 - 1 if index < 9 else 10000,
                "resolved_sample_count": total,
                "mean_probability": round(probabilities / total / 10000, 6),
                "observed_frequency": round(positives / total, 6),
            }
            for index, (total, probabilities, positives) in enumerate(buckets) if total
        ],
    }


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
