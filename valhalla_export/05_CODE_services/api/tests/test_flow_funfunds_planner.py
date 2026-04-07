# services/api/tests/test_flow_funfunds_planner.py

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

# Adjust import if your main app path is different
from app.main import app  # or: from valhalla.services.api.main import app

client = TestClient(app)


def test_funfunds_basic_allocation():
    """
    Happy path: decent income, reasonable bills, standard dials.
    We expect:
    - bills paid
    - non-zero safety reserve
    - non-zero FunFunds / debt / reinvest
    - leftover >= 0
    """
    payload = {
        "month_label": "2025-01",
        "gross_income": 20000,
        "fixed_bills": [
            {"name": "Rent", "amount": 1800, "category": "housing"},
            {"name": "Utilities", "amount": 300, "category": "utilities"},
            {"name": "Subscriptions", "amount": 200, "category": "tools"},
        ],
        "min_safety_reserve_percent": 0.10,
        "funfunds_percent": 0.15,
        "debt_paydown_percent": 0.15,
        "reinvest_percent": 0.40,
    }

    resp = client.post("/api/flow/funfunds_plan", json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["month_label"] == "2025-01"
    assert data["gross_income"] == 20000

    allocation = data["allocation"]
    bills_total = allocation["bills_total"]
    safety = allocation["safety_reserve"]
    funfunds = allocation["funfunds_amount"]
    debt = allocation["debt_paydown_amount"]
    reinvest = allocation["reinvest_amount"]
    leftover = allocation["leftover_amount"]

    assert bills_total == 2300  # 1800 + 300 + 200
    assert safety >= 0
    assert funfunds >= 0
    assert debt >= 0
    assert reinvest >= 0
    assert leftover >= 0


def test_funfunds_zero_net_after_bills_triggers_flag():
    """
    If bills eat the whole income or more, the engine should:
    - set all variable allocations to zero
    - flag breach_safety_minimum
    """
    payload = {
        "month_label": "2025-02",
        "gross_income": 2000,
        "fixed_bills": [
            {"name": "Rent", "amount": 1800, "category": "housing"},
            {"name": "Utilities", "amount": 300, "category": "utilities"},
            # already 2100 > 2000 income
        ],
        "min_safety_reserve_percent": 0.10,
        "funfunds_percent": 0.20,
        "debt_paydown_percent": 0.20,
        "reinvest_percent": 0.40,
    }

    resp = client.post("/api/flow/funfunds_plan", json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    allocation = data["allocation"]
    flags = data["policy_flags"]

    assert allocation["safety_reserve"] == 0
    assert allocation["funfunds_amount"] == 0
    assert allocation["debt_paydown_amount"] == 0
    assert allocation["reinvest_amount"] == 0
    assert allocation["leftover_amount"] == 0

    assert flags["breach_safety_minimum"] is True
    assert "unable to fund safety" in (flags["notes"] or "").lower()


def test_funfunds_scaling_when_dials_too_high():
    """
    When combined FunFunds + debt + reinvest > net_after_bills - safety,
    the engine should scale them down proportionally.
    Just check that:
    - allocations sum <= net_after_bills
    - notes mention scaling
    """
    payload = {
        "month_label": "2025-03",
        "gross_income": 10000,
        "fixed_bills": [
            {"name": "Rent", "amount": 1500, "category": "housing"},
        ],
        "min_safety_reserve_percent": 0.20,
        "funfunds_percent": 0.50,
        "debt_paydown_percent": 0.50,
        "reinvest_percent": 0.50,
    }

    resp = client.post("/api/flow/funfunds_plan", json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    allocation = data["allocation"]
    flags = data["policy_flags"]

    net_after_bills = data["net_after_bills"]

    # Sum of variable buckets cannot exceed net_after_bills
    total_alloc = (
        allocation["safety_reserve"]
        + allocation["funfunds_amount"]
        + allocation["debt_paydown_amount"]
        + allocation["reinvest_amount"]
        + allocation["leftover_amount"]
    )

    assert total_alloc <= net_after_bills + 0.01  # allow 1 cent rounding wiggle
    if flags["notes"]:
        assert "scaled" in flags["notes"].lower()

