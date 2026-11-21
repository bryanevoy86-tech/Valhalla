"""Issue prospective, scope-specific baseline estimates from observed receipts."""
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models.completion_registry import LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.norns_forecast import NornsForecast, NornsHoldout
from app.services.prime_business_execution import ACTION_TYPE, _json, _receipt_id, action_status


SOURCE = "SCOPED_HISTORICAL_RATE"


def issue_scoped_estimate(db: Session, scope: dict, now, horizon_seconds: int) -> dict:
    work, forecast = LegacyInstanceWorkItem, NornsForecast
    filters = [getattr(work, key) == value for key, value in scope.items()]
    horizon = timedelta(seconds=horizon_seconds)
    history = db.scalars(select(forecast).join(work, work.action_id == forecast.action_id).where(
        *filters, forecast.observed_outcome.is_not(None), forecast.resolved_at < now,
        ~exists(select(NornsHoldout.forecast_id).where(NornsHoldout.forecast_id == forecast.id)),
    ).order_by(forecast.resolved_at.desc(), forecast.id).limit(100)).all()
    sample = []
    for past in history:
        if past.deadline_at - past.issued_at != horizon:
            continue
        if past.evidence_ref == _receipt_id(past.action_id):
            if not action_status(db, past.action_id)["internal_artifact_verified"]:
                continue
        elif not (past.observed_outcome == 0 and past.resolved_at >= past.deadline_at
                  and past.evidence_ref == f"FACTORY_DEADLINE_NO_RECEIPT:{past.action_id}"):
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
