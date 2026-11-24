from sqlalchemy.orm import Session

from app.policies.models import ClonePolicy, MirrorPolicy, PolicyEventLog, PolicyGateMetric


def test_clone_and_mirror_readiness_does_not_dispatch_or_start_cooldown(deal_client):
    client, engine = deal_client
    for model in (ClonePolicy, MirrorPolicy, PolicyEventLog, PolicyGateMetric):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add(ClonePolicy(
            enabled=True, min_days_between=7, max_active=5, required_uptime_pct=99,
            required_cash_reserves=100, required_net_margin_pct=5, required_audit_score=90,
            max_error_rate_ppm=100,
        ))
        db.add(MirrorPolicy(
            enabled=True, min_days_between=7, max_active=2,
            required_p90_rps=10, required_p95_latency_ms=100,
        ))
        db.commit()

    snapshot = {
        "uptime_pct": 99.9, "cash_reserves": 500, "net_margin_pct": 10,
        "audit_score": 99, "error_rate_ppm": 25, "traffic_p90_rps": 20, "latency_p95_ms": 120,
    }
    for kind in ("clone", "mirror"):
        trigger = f"/policies/{kind}/trigger"
        assert client.post(trigger, headers={"X-Prime-Control-Key": "wrong"}, json=snapshot).status_code == 401
        ready = client.post(f"/policies/{kind}/evaluate", json=snapshot)
        assert ready.status_code == 200, ready.text
        assert ready.json()["allow"] is True
        blocked = client.post(trigger, json=snapshot)
        assert blocked.status_code == 200, blocked.text
        assert blocked.json()["allow"] is False
        assert "no dispatcher is configured" in blocked.json()["reason"]

    with Session(engine) as db:
        assert db.query(ClonePolicy).one().last_triggered_at is None
        assert db.query(MirrorPolicy).one().last_triggered_at is None
        assert db.query(PolicyGateMetric).count() == 2
        decisions = db.query(PolicyEventLog).order_by(PolicyEventLog.id).all()
        assert [(event.kind, event.decision) for event in decisions] == [
            ("clone", "allow"), ("clone", "deny"), ("mirror", "allow"), ("mirror", "deny"),
        ]
