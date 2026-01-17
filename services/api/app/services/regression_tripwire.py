from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.kpi_event import KPIEvent
from app.models.regression_policy import RegressionPolicy
from app.models.regression_state import RegressionState

# Reuse your risk/go-live enforcement levers:
from app.services.risk_guard import _get_policy as _get_risk_policy  # internal but ok here
from app.services.go_live import set_kill_switch


def _rate_from_events(events: list[KPIEvent]) -> Optional[float]:
    # For binary outcomes: rate = successes / count(success not null)
    binary = [e for e in events if e.success is not None]
    if binary:
        total = len(binary)
        succ = sum(1 for e in binary if e.success)
        return succ / total if total > 0 else None

    # For numeric events: rate = average value
    numeric = [e for e in events if e.value is not None]
    if numeric:
        total = len(numeric)
        s = sum(float(e.value) for e in numeric)
        return s / total if total > 0 else None

    return None


def _get_or_create_state(db: Session, domain: str, metric: str) -> RegressionState:
    row = db.query(RegressionState).filter(
        RegressionState.domain == domain, RegressionState.metric == metric
    ).first()
    if row:
        return row
    row = RegressionState(domain=domain, metric=metric, triggered=False, last_checked_at=datetime.utcnow())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def evaluate(db: Session, domain: str, metric: str, actor: Optional[str] = None) -> RegressionState:
    domain = domain.strip().upper()
    metric = metric.strip().lower()

    pol = db.query(RegressionPolicy).filter(
        RegressionPolicy.domain == domain, RegressionPolicy.metric == metric
    ).first()
    if not pol or not pol.enabled:
        st = _get_or_create_state(db, domain, metric)
        st.last_checked_at = datetime.utcnow()
        st.note = "policy_missing_or_disabled"
        db.add(st)
        db.commit()
        db.refresh(st)
        return st

    # Pull recent events
    q = db.query(KPIEvent).filter(KPIEvent.domain == domain, KPIEvent.metric == metric).order_by(KPIEvent.created_at.desc())

    recent = q.limit(pol.window_events).all()
    baseline = q.offset(pol.window_events).limit(pol.baseline_events).all()

    st = _get_or_create_state(db, domain, metric)
    st.last_checked_at = datetime.utcnow()

    if len(recent) < pol.min_events_to_enforce or len(baseline) < pol.min_events_to_enforce:
        st.note = f"insufficient_events(recent={len(recent)}, baseline={len(baseline)})"
        db.add(st)
        db.commit()
        db.refresh(st)
        return st

    current_rate = _rate_from_events(recent)
    baseline_rate = _rate_from_events(baseline)

    st.current = current_rate
    st.baseline = baseline_rate

    if current_rate is None or baseline_rate is None or baseline_rate <= 0:
        st.note = "cannot_compute_rate"
        db.add(st)
        db.commit()
        db.refresh(st)
        return st

    drop = (baseline_rate - current_rate) / baseline_rate
    st.drop_fraction = drop

    triggered = drop >= float(pol.max_drop_fraction)
    st.triggered = bool(triggered)

    if triggered:
        st.last_triggered_at = datetime.utcnow()
        st.note = f"TRIGGERED drop={drop:.3f} action={pol.action}"

        # Action: throttle by disabling the engine's risk policy, OR kill-switch.
        if pol.action.upper() == "THROTTLE":
            rp = _get_risk_policy(db, domain)  # creates if missing (default disabled safe)
            rp.enabled = False
            rp.changed_by = actor or "system"
            rp.reason = f"Regression tripwire: {domain}.{metric} drop={drop:.3f}"
            rp.updated_at = datetime.utcnow()
            db.add(rp)
            db.commit()

        elif pol.action.upper() == "KILL_SWITCH":
            set_kill_switch(db, True, changed_by=actor or "system", reason=f"Regression tripwire: {domain}.{metric}")

    else:
        st.note = f"OK drop={drop:.3f}"

    db.add(st)
    db.commit()
    db.refresh(st)
    return st
