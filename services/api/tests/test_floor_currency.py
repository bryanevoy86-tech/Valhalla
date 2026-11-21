from app.models.revenue_ledger import RevenueLedger
from app.models.trajectory_target import TrajectoryTarget


def test_private_floor_targets_keep_currencies_separate_and_label_unreconciled_amounts(deal_client, monkeypatch):
    client, engine = deal_client
    key = "floor-fixture-owner-key"
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", key)
    owner = {"X-Owner-Mandate-Key": key}
    for model in (RevenueLedger, TrajectoryTarget):
        model.__table__.create(engine)
    root = "/api/governance/floor"
    event = {"engine_code": "saas-test", "gross_amount": "120.01", "currency": "CAD", "as_of_date": "2026-12-28"}
    assert client.post(f"{root}/revenue/record", json=event).status_code == 401
    for override in ({}, {"currency": "USD", "gross_amount": "500.00"}, {"as_of_date": "2027-01-01"}):
        posted = client.post(f"{root}/revenue/record", headers=owner, json={**event, **override})
        assert posted.status_code == 200, posted.text
        assert posted.json()["verified_commercial_revenue"] is False
    target = client.post(f"{root}/targets/upsert", headers=owner, json={
        "engine_code": "saas-test", "month": "2026-12-01", "currency": "CAD", "min_gross": 100,
    })
    assert target.status_code == 200, target.text
    month = client.get(f"{root}/trajectory/month", params={"engine_code": "saas-test", "month": "2026-12-31"})
    assert month.status_code == 200, month.text
    assert month.json()["actual_gross"] == 120.01
    assert month.json()["actual_fun_fund"] == 12
    assert month.json()["basis"] == "RECORDED_UNRECONCILED_LEDGER"
    assert month.json()["verified_commercial_revenue"] is False
