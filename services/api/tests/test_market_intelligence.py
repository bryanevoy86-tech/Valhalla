"""Canonical HTTP rehearsals with synthetic inputs and no financial effects."""
from datetime import datetime, timedelta, timezone
import json
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.arbitrage.models import FXMetric, FXOrder, FXRule
from app.finops.models import VaultBalance
from app.loki.analyst import challenge
from app.loki.models import LokiFinding, LokiIndependentReceipt, LokiReconsideration, LokiReview
from app.loki.specialist_review import require_reviewed_reports
from app.models.completion_registry import (
    LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, SourceRegistryItem,
)
from app.models.market_intelligence import MarketEvidence
from app.models.norns_forecast import NornsMarketForecast
from app.routers import market_intelligence, norns_market
from app.models.revenue_ledger import RevenueLedger
from app.models.specialist_assignment import SpecialistAssignment
from app.pantheon.monitor import run_assignment
from app.services.owner_operating_brief import operating_evidence


MARKET = "/api/prime/market"
PANTHEON = "/api/prime/pantheon"
SCOPE = {"legacy_instance_id": "north-treasury-legacy", "business_id": "treasury", "engine_id": "invest", "jurisdiction": "CA-MB"}
MIRROR = {**SCOPE, "legacy_instance_id": "east-treasury-mirror", "jurisdiction": "CA-ON"}
OWNER = {"X-Owner-Mandate-Key": "market-isolated-owner"}


@pytest.fixture
def market_client(deal_client, monkeypatch):
    client, engine = deal_client
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", OWNER["X-Owner-Mandate-Key"])
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    for model in (LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, SourceRegistryItem,
                  MarketEvidence, NornsMarketForecast, RevenueLedger, SpecialistAssignment, LokiReview, LokiFinding,
                  LokiIndependentReceipt, LokiReconsideration):
        model.__table__.create(engine)
    with Session(engine) as db:
        for scope in (SCOPE, MIRROR):
            db.add(LegacyInstanceRegistryItem(legacy_instance_id=scope["legacy_instance_id"],
                   display_name="Paper treasury", status="PASS", synchronization_status="SYNCED",
                   engines_json='["invest"]', assigned_businesses_json='["treasury"]',
                   assigned_jurisdictions_json=json.dumps([scope["jurisdiction"]]),
                   local_knowledge_context_json=json.dumps(scope)))
        db.add(SourceRegistryItem(source_id="internal-fixture", canonical_name="Synthetic fixture", data_class="synthetic",
                                 source_type="fixture", terminal_state="PASS",
                                 mode_allowlist_json='["practice"]', permission_status="allowed"))
        db.add(SourceRegistryItem(source_id="outcome-fixture", canonical_name="Separate outcome fixture", data_class="synthetic",
                                 source_type="fixture", terminal_state="PASS", mode_allowlist_json='["practice"]'))
        db.commit()
    return client, engine


def record(client, data, *, scope=SCOPE, source_id="internal-fixture"):
    payload = {"scope": scope, "source_id": source_id, "source_ref": "fixture:market-input",
               "evidence_id": str(uuid4()), "rights": "AUTHORIZED_INTERNAL_RESEARCH",
               "evidence_class": "SIMULATION", "data": data}
    response = client.post(f"{MARKET}/evidence", headers=OWNER, json=payload)
    assert response.status_code == 201, response.text
    assert client.post(f"{MARKET}/evidence", headers=OWNER, json=payload).json() == response.json()
    return payload["evidence_id"]


def test_investment_replay_is_source_bound_and_does_not_look_ahead(market_client):
    client, engine = market_client
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)

    def dataset(symbol, prices, asset_class):
        bars = [{"at": (cutoff - timedelta(days=len(prices) - index - 1)).isoformat(),
                 "open": str(close if index != 3 else prices[2]), "close": str(close),
                 "dividend": "1" if index == 4 else "0"} for index, close in enumerate(prices)]
        return {"kind": "SECURITY", "asset_class": asset_class, "symbol": symbol, "currency": "CAD",
                "sector": "utilities" if asset_class == "STOCK" else "index",
                "price_basis": "UNADJUSTED_SPLIT_FREE", "bars": bars,
                "fundamentals": {"available_at": cutoff.isoformat(), "earnings_per_share": "5", "annual_distribution": "2"}}

    holding = record(client, dataset("FICTION", [10, 11, 12, 20, 22, 9], "STOCK"))
    benchmark = record(client, dataset("BENCH", [10, 10, 10, 11, 12, 13], "ETF"))
    research = client.get(f"{MARKET}/evidence/{holding}/research").json()
    assert research["research"]["price_to_earnings"] == "1.80000000"
    assert research["research"]["moving_average_samples"] == 6
    macro = record(client, {"kind": "MACRO", "topic": "CAPITAL_FLOW", "published_at": cutoff.isoformat(),
                            "summary": "Synthetic jurisdiction capital-flow release", "reported_measure": "fixture CAD 10M"})
    assert client.get(f"{MARKET}/evidence/{macro}/research").json()["research"]["topic"] == "CAPITAL_FLOW"
    request = {"run_id": str(uuid4()), "scope": SCOPE, "as_of": cutoff.isoformat(),
               "portfolio": [{"dataset_id": holding, "weight_bp": 10000}], "benchmark_id": benchmark,
               "capital": "120", "strategy": "CLOSE_ABOVE_MOVING_AVERAGE", "lookback": 3,
               "slippage_bp": 25, "half_spread_bp": 25, "commission": "1"}
    endpoint = f"{MARKET}/replays/investment"
    assert client.post(endpoint, json=request).status_code == 401
    assert client.post(endpoint, headers=OWNER, json={**request, "scope": MIRROR}).status_code == 409
    assert client.post(endpoint, headers=OWNER, json={
        **request, "as_of": (cutoff - timedelta(seconds=1)).isoformat(),
    }).status_code == 422
    response = client.post(endpoint, headers=OWNER, json=request)
    assert response.status_code == 201, response.text
    receipt = response.json()
    assert receipt["basis"] == "HISTORICAL_PAPER_SIMULATION"
    assert receipt["result"]["paper_fills"] == 1
    assert receipt["result"]["paper_distributions"] == "9.00000000"
    assert receipt["result"]["estimated_execution_costs"] == "1.54000000"
    assert receipt["result"]["marked_equity"] == "100.46000000"
    assert receipt["result"]["benchmark_relative_return_fraction"].startswith("-")
    assert not receipt["verified_real_world_outcome"]
    assert client.get(f"{MARKET}/replays/{request['run_id']}").json() == receipt
    assert client.post(endpoint, headers=OWNER, json=request).json() == receipt
    assert client.post(endpoint, headers=OWNER, json={**request, "capital": "121"}).status_code == 409
    assert client.delete(f"{MARKET}/evidence/{benchmark}", headers=OWNER).json()["revoked"]
    assert client.post(endpoint, headers=OWNER, json=request).status_code == 409
    assert client.get(f"{MARKET}/replays/{request['run_id']}").json() == receipt
    with Session(engine) as db:
        assert db.query(RevenueLedger).count() == 0


def test_fx_triangle_conversion_and_interruption_reconcile_without_live_authority(market_client, monkeypatch):
    client, engine = market_client
    at = datetime.now(timezone.utc) - timedelta(minutes=5)

    def quote(venue, base, counter, bid, ask, depth="1000", delay=1):
        return {"quote_id": str(uuid4()), "venue": venue, "base": base, "counter": counter, "bid": bid, "ask": ask,
                "bid_depth_base": depth, "ask_depth_base": depth, "at": at.isoformat(),
                "expires_at": (at + timedelta(seconds=45)).isoformat(), "fee_bp": 10, "settlement_seconds": delay,
                "origin_ref": f"fixture:{venue}:{base}{counter}"}

    batch = record(client, {"kind": "FX", "quotes": [
        quote("VENUE_A", "CAD", "USD", "0.75", "0.76"),
        quote("VENUE_B", "USD", "EUR", "0.91", "0.92"),
        quote("VENUE_C", "EUR", "CAD", "1.50", "1.51"),
        quote("VENUE_D", "CAD", "USD", "0.77", "0.78", depth="2"),
        quote("VENUE_E", "USD", "CAD", "1.40", "1.41"),
    ]})
    request = {"run_id": str(uuid4()), "scope": SCOPE, "as_of": at.isoformat(), "dataset_id": batch,
               "mode": "TRIANGLE", "start_currency": "CAD", "amount": "100", "exposure_limit": "200",
               "max_age_seconds": 20, "max_settlement_seconds": 5, "slippage_bp": 10}
    endpoint = f"{MARKET}/replays/fx"

    def run(**overrides):
        response = client.post(endpoint, headers=OWNER, json={**request, "run_id": str(uuid4()), **overrides})
        assert response.status_code == 201, response.text
        assert response.json()["external_execution_authorized"] is False
        return response.json()["result"]

    tri = run()
    assert tri["status"] == "SIMULATED" and tri["paper_loop_pnl"] == "1.75"
    assert {item["venue"] for item in tri["paper_legs"]} == {"VENUE_A", "VENUE_B", "VENUE_C"}
    assert run() == tri
    direct = run(mode="BEST_DIRECT", target_currency="USD")
    assert direct["paper_balances"] == {"CAD": "0.00", "USD": "74.85"}
    assert direct["paper_loop_pnl"] is None
    loop = run(mode="CROSS_VENUE_LOOP")
    assert loop["paper_loop_pnl"] == "4.58"
    interrupted = run(failure_at_leg=2, partial_fill_bp=5000)
    assert interrupted["status"] == "INTERRUPTED" and interrupted["paper_loop_pnl"] is None
    assert interrupted["paper_balances"] == {"CAD": "0.00", "EUR": "33.98", "USD": "37.43"}
    assert run(max_settlement_seconds=2)["status"] == "NO_FEASIBLE_ROUTE"
    assert run(as_of=(at + timedelta(seconds=21)).isoformat())["status"] == "NO_FEASIBLE_ROUTE"
    assert client.post(endpoint, headers=OWNER, json={**request, "exposure_limit": "50"}).status_code == 422
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    assert client.post(endpoint, headers=OWNER, json=request).status_code == 503

    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    for role in ("MIMIR", "LOKI", "NJORD", "TYR"):
        result = client.post(f"{PANTHEON}/assignments", headers=OWNER, json={
            **SCOPE, "assignment_id": str(uuid4()), "role": role, "cadence_seconds": 300, "duration_seconds": 600,
        })
        assert result.status_code == 201, result.text
        with Session(engine) as db:
            report_id = run_assignment(db, role)["report_event_id"]
        report = client.get(f"{PANTHEON}/reports/{report_id}").json()
        market = report["observations"]["market_intelligence"]
        assert "FX_QUOTES_EXPIRED_OR_TOO_OLD" in market["alerts"]
        if role == "MIMIR":
            assert market["replay_receipts"][0]["kind"] == "FX"
            assert not market["verified_real_world_outcomes"]
    with Session(engine) as db:
        with pytest.raises(HTTPException, match="requires independent"):
            require_reviewed_reports(db, [report_id], SCOPE)
        assert operating_evidence(db)["latest_market_alerts"]
        assert db.query(RevenueLedger).count() == 0
    response = client.post(f"{PANTHEON}/reports/{report_id}/challenge")
    assert response.status_code == 201, response.text
    with Session(engine) as db:
        review = db.query(LokiReview).one()
        finding = challenge({"artifact_type": "pantheon_report", "reference": report_id,
                             "raw_input": review.raw_input, "artifact_sha256": review.artifact_sha256})
        assert any(item.category == "market_simulation" and item.material for item in finding.findings)


def test_legacy_paper_metric_never_compounds_into_treasury(deal_client, monkeypatch):
    client, engine = deal_client
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", OWNER["X-Owner-Mandate-Key"])
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    for model in (FXRule, FXOrder, FXMetric, VaultBalance):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add(VaultBalance(vault_code="MAIN", balance=250, currency="CAD"))
        db.add(FXMetric(equity=9999999, peak_equity=9999999, note="auto"))
        db.commit()
    payload = {"pair": "USD/CAD", "side": "buy", "size": 100, "entry_px": 1.2}
    assert client.post("/arbitrage/orders", json=payload).status_code == 401
    created = client.post("/arbitrage/orders", headers=OWNER, json=payload)
    assert created.status_code == 200, created.text
    order_id = created.json()["id"]
    assert created.json()["basis"] == "LEGACY_PAPER_BOOK"
    assert client.post(f"/arbitrage/orders/{order_id}/close", headers=OWNER, json={"exit_px": 1.3}).status_code == 200
    assert client.post(f"/arbitrage/orders/{order_id}/close", headers=OWNER, json={"exit_px": 1.4}).status_code == 409
    for _ in range(2):
        response = client.post("/arbitrage/metrics/eval", headers=OWNER)
        assert response.status_code == 200, response.text
        assert response.json()["equity"] == response.json()["peak_equity"] == 100010
    with Session(engine) as db:
        assert db.query(VaultBalance).one().balance == 250


def test_prospective_norns_holdout_requires_pinned_outcome_and_separates_calibration(market_client, monkeypatch):
    client, _ = market_client
    issued = datetime(2026, 10, 10, 14, tzinfo=timezone.utc)
    target = issued + timedelta(days=1)
    clock = [issued]
    monkeypatch.setattr(market_intelligence, "now", lambda: clock[0])
    monkeypatch.setattr(norns_market, "now", lambda: clock[0])
    root = "/api/prime/norns/market"

    def series(at, close):
        return {"kind": "SECURITY", "symbol": "BOND01", "asset_class": "BOND", "sector": "government",
                "currency": "CAD", "price_basis": "UNADJUSTED_SPLIT_FREE",
                "bars": [{"at": (at - timedelta(days=days)).isoformat(), "open": "100", "close": close}
                         for days in (3, 2, 1, 0)],
                "fundamentals": {"available_at": at.isoformat(), "bond_yield_bp": 430, "duration_years": "5.4"}}

    baseline = record(client, series(issued - timedelta(days=1), "100"))
    req = {"forecast_id": str(uuid4()), "scope": SCOPE, "baseline_evidence_id": baseline,
           "target_date": target.date().isoformat(), "threshold_close": "100",
           "probability_bp": 6000, "cohort": "HOLDOUT", "outcome_source_id": "outcome-fixture"}
    assert client.post(f"{root}/forecasts", headers=OWNER, json={
        **req, "outcome_source_id": "internal-fixture",
    }).status_code == 409
    created = client.post(f"{root}/forecasts", headers=OWNER, json=req)
    assert created.status_code == 201, created.text
    assert created.json()["estimate_source"] == "OWNER_PROBABILITY"
    assert client.post(f"{root}/forecasts", headers=OWNER, json={
        **req, "forecast_id": str(uuid4()), "probability_bp": 9000,
    }).status_code == 409
    url = f"{root}/forecasts/{req['forecast_id']}/resolve"
    assert client.post(url, headers=OWNER, json={"outcome_evidence_id": baseline}).status_code == 409
    clock[0] = target + timedelta(days=1)
    wrong_source = record(client, series(target, "102"))
    outcome = record(client, series(target, "102"), source_id="outcome-fixture")
    conflict = record(client, series(target, "99"), source_id="outcome-fixture")
    assert client.post(url, headers=OWNER, json={"outcome_evidence_id": wrong_source}).status_code == 409
    assert client.post(url, headers=OWNER, json={"outcome_evidence_id": outcome}).status_code == 409
    assert client.delete(f"{MARKET}/evidence/{conflict}", headers=OWNER).status_code == 200
    resolved = client.post(url, headers=OWNER, json={"outcome_evidence_id": outcome})
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["settlement"]["observed_outcome"] == 1

    def calibrate(scope, cohort="HOLDOUT"):
        response = client.post(f"{root}/calibration", params={"evidence_class": "SIMULATION", "cohort": cohort}, json=scope)
        assert response.status_code == 200, response.text
        return response.json()

    assert calibrate(SCOPE)["brier_score"] == 0.16
    assert calibrate(SCOPE, "PROSPECTIVE")["resolved_sample_count"] == 0
    assert calibrate(MIRROR)["resolved_sample_count"] == 0
    assert client.delete(f"{MARKET}/evidence/{outcome}", headers=OWNER).status_code == 200
    assert calibrate(SCOPE)["excluded_sample_count"] == 1


def test_scoped_treasury_scenario_keeps_reserves_household_and_fun_funds_in_balance(market_client):
    client, engine = market_client
    endpoint = "/api/governance/floor/wealth/scenarios"
    request = {"scenario_id": str(uuid4()), "scope": SCOPE, "month": "2026-11-01", "currency": "CAD",
               "years_from_launch": 1, "evidence_class": "ASSUMPTION", "net_business_cash_minor": 100001,
               "available_operating_reserve_minor": 10000, "target_operating_reserve_minor": 20000,
               "target_owner_compensation_minor": 35000, "other_household_income_minor": 1000,
               "fun_fund_cap_minor": 2500, "simulate_withdrawal": True,
               "household_lines": [{"category": "HOUSING", "budget_minor": 30000, "expenditure_minor": 40000}]}
    assert client.post(endpoint, json=request).status_code == 401
    first = client.post(endpoint, headers=OWNER, json=request)
    assert first.status_code == 201, first.text
    result = first.json()["result"]
    assert result["tracked_fun_fund_retained_minor"] == 5500
    assert result["planned_reinvestment_minor"] == 49501
    assert result["modeled_fun_fund_withdrawal_minor"] == 0
    assert result["household"]["income_less_expenditure_minor"] == -4000
    assert result["operating_reserve_addition_minor"] + result["planned_owner_compensation_minor"] + result[
        "planned_reinvestment_minor"] + result["fun_fund_accrual_minor"] == request["net_business_cash_minor"]
    assert client.post(endpoint, headers=OWNER, json=request).json() == first.json()
    assert client.post(endpoint, headers=OWNER, json={**request, "scope": MIRROR}).status_code == 409
    later = client.post(endpoint, headers=OWNER, json={**request, "scenario_id": str(uuid4()), "years_from_launch": 2})
    assert later.json()["result"]["modeled_fun_fund_withdrawal_minor"] == 2500
    assert later.json()["result"]["funds_movement_authorized"] is False
    with Session(engine) as db:
        assert db.query(RevenueLedger).count() == 0
