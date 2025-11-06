import json
import datetime
from sqlalchemy.orm import Session
from app.policies.models import (
    PolicyGateMetric,
    ClonePolicy,
    MirrorPolicy,
    PolicyEventLog,
)


def _days_since(dt: datetime.datetime | None) -> int:
    if not dt:
        return 10_000
    return (datetime.datetime.utcnow() - dt).days


def evaluate_clone(db: Session, snap: dict) -> tuple[bool, str]:
    policy = db.query(ClonePolicy).order_by(ClonePolicy.id.asc()).first()
    if not policy or not policy.enabled:
        return False, "Clone policy disabled or missing."
    if _days_since(policy.last_triggered_at) < policy.min_days_between:
        return False, f"Cooldown active: {_days_since(policy.last_triggered_at)}d < {policy.min_days_between}d."
    checks = [
        (
            snap["uptime_pct"] >= policy.required_uptime_pct,
            f"uptime {snap['uptime_pct']}% >= {policy.required_uptime_pct}%",
        ),
        (
            snap["cash_reserves"] >= float(policy.required_cash_reserves),
            f"cash {snap['cash_reserves']} >= {policy.required_cash_reserves}",
        ),
        (
            snap["net_margin_pct"] >= policy.required_net_margin_pct,
            f"margin {snap['net_margin_pct']}% >= {policy.required_net_margin_pct}%",
        ),
        (
            snap["audit_score"] >= policy.required_audit_score,
            f"audit {snap['audit_score']} >= {policy.required_audit_score}",
        ),
        (
            snap["error_rate_ppm"] <= policy.max_error_rate_ppm,
            f"errors {snap['error_rate_ppm']} <= {policy.max_error_rate_ppm}",
        ),
    ]
    ok = all(c[0] for c in checks)
    reason = "; ".join(["OK" if c[0] else f"FAIL:{c[1]}" for c in checks])
    return ok, reason


def evaluate_mirror(db: Session, snap: dict) -> tuple[bool, str]:
    policy = db.query(MirrorPolicy).order_by(MirrorPolicy.id.asc()).first()
    if not policy or not policy.enabled:
        return False, "Mirror policy disabled or missing."
    if _days_since(policy.last_triggered_at) < policy.min_days_between:
        return False, f"Cooldown active: {_days_since(policy.last_triggered_at)}d < {policy.min_days_between}d."
    p90 = snap.get("traffic_p90_rps") or 0.0
    p95 = snap.get("latency_p95_ms") or 10_000.0
    checks = [
        (p90 >= policy.required_p90_rps, f"p90_rps {p90} >= {policy.required_p90_rps}"),
        (
            p95 >= policy.required_p95_latency_ms,
            f"latency_p95 {p95}ms >= {policy.required_p95_latency_ms}ms",
        ),
    ]
    ok = all(c[0] for c in checks)
    reason = "; ".join(["OK" if c[0] else f"FAIL:{c[1]}" for c in checks])
    return ok, reason


def log_event(db: Session, kind: str, decision: bool, reason: str, snap: dict):
    db.add(
        PolicyEventLog(
            kind=kind,
            decision="allow" if decision else "deny",
            reason=reason,
            snapshot_json=json.dumps(snap),
        )
    )
    db.commit()


def touch_last_trigger(db: Session, kind: str):
    now = datetime.datetime.utcnow()
    if kind == "clone":
        p = db.query(ClonePolicy).first()
    else:
        p = db.query(MirrorPolicy).first()
    if p:
        p.last_triggered_at = now
        db.commit()
