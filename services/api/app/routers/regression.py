from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.kpi_event import KPIEvent
from app.models.regression_policy import RegressionPolicy
from app.models.regression_state import RegressionState
from app.services.regression_tripwire import evaluate

router = APIRouter(prefix="/governance/regression", tags=["Governance", "Regression"])


@router.get("/policies", response_model=list[dict])
def list_policies(db: Session = Depends(get_db)):
    rows = db.query(RegressionPolicy).order_by(RegressionPolicy.domain.asc(), RegressionPolicy.metric.asc()).all()
    return [{
        "domain": r.domain, "metric": r.metric, "window_events": r.window_events,
        "baseline_events": r.baseline_events, "min_events_to_enforce": r.min_events_to_enforce,
        "max_drop_fraction": r.max_drop_fraction, "action": r.action, "enabled": r.enabled,
        "changed_by": r.changed_by, "reason": r.reason, "updated_at": r.updated_at,
    } for r in rows]


@router.post("/policies/upsert", response_model=dict)
def upsert_policy(
    domain: str,
    metric: str,
    window_events: int = 50,
    baseline_events: int = 200,
    min_events_to_enforce: int = 50,
    max_drop_fraction: float = 0.20,
    action: str = "THROTTLE",
    enabled: bool = True,
    changed_by: str = "bryan",
    reason: str | None = None,
    db: Session = Depends(get_db),
):
    domain_u = domain.strip().upper()
    metric_l = metric.strip().lower()

    row = db.query(RegressionPolicy).filter(
        RegressionPolicy.domain == domain_u, RegressionPolicy.metric == metric_l
    ).first()
    if not row:
        row = RegressionPolicy(domain=domain_u, metric=metric_l)
        db.add(row)

    row.window_events = int(window_events)
    row.baseline_events = int(baseline_events)
    row.min_events_to_enforce = int(min_events_to_enforce)
    row.max_drop_fraction = float(max_drop_fraction)
    row.action = action.strip().upper()
    row.enabled = bool(enabled)
    row.changed_by = changed_by
    row.reason = reason
    db.add(row)
    db.commit()
    db.refresh(row)

    return {"ok": True, "policy": {
        "domain": row.domain, "metric": row.metric, "window_events": row.window_events,
        "baseline_events": row.baseline_events, "min_events_to_enforce": row.min_events_to_enforce,
        "max_drop_fraction": row.max_drop_fraction, "action": row.action, "enabled": row.enabled
    }}


@router.get("/state", response_model=list[dict])
def list_state(db: Session = Depends(get_db)):
    rows = db.query(RegressionState).order_by(RegressionState.domain.asc(), RegressionState.metric.asc()).all()
    return [{
        "domain": r.domain, "metric": r.metric, "triggered": r.triggered,
        "baseline": r.baseline, "current": r.current, "drop_fraction": r.drop_fraction,
        "last_checked_at": r.last_checked_at, "last_triggered_at": r.last_triggered_at, "note": r.note
    } for r in rows]


@router.post("/evaluate", response_model=dict)
def evaluate_one(domain: str, metric: str, actor: str = "bryan", db: Session = Depends(get_db)):
    st = evaluate(db, domain=domain, metric=metric, actor=actor)
    return {"ok": True, "state": {
        "domain": st.domain, "metric": st.metric, "triggered": st.triggered,
        "baseline": st.baseline, "current": st.current, "drop_fraction": st.drop_fraction,
        "note": st.note
    }}


@router.post("/kpi", response_model=dict)
def record_kpi(
    domain: str,
    metric: str,
    success: bool | None = None,
    value: float | None = None,
    actor: str | None = None,
    correlation_id: str | None = None,
    detail: str | None = None,
    db: Session = Depends(get_db),
):
    e = KPIEvent(
        domain=domain.strip().upper(),
        metric=metric.strip().lower(),
        success=success,
        value=value,
        actor=actor,
        correlation_id=correlation_id,
        detail=detail,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"ok": True, "id": e.id}
