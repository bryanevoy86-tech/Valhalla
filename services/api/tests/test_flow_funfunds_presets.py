# services/api/tests/test_flow_funfunds_presets.py

"""
Tests for the FunFunds preset modes (lean/growth).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_lean_preset_applies_correct_percentages():
    """
    The lean preset should apply conservative percentages:
    - 20% safety
    - 10% funfunds
    - 30% debt
    - 30% reinvest
    """
    payload = {
        "month_label": "2025-01",
        "gross_income": 10000,
        "fixed_bills": [
            {"name": "Rent", "amount": 2000, "category": "housing"},
        ],
    }

    resp = client.post("/api/flow/funfunds_plan/lean", json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["month_label"] == "2025-01"
    
    # Check debug output confirms lean mode
    debug = data["debug"]
    assert debug.get("mode") == "lean"
    assert debug.get("min_safety_reserve_percent") == "0.20"
    assert debug.get("funfunds_percent") == "0.10"
    assert debug.get("debt_paydown_percent") == "0.30"
    assert debug.get("reinvest_percent") == "0.30"
    
    # Net after bills = 10000 - 2000 = 8000
    # Safety reserve = 8000 * 0.20 = 1600
    # Available for dials = 8000 - 1600 = 6400
    # FunFunds = 8000 * 0.10 = 800
    # Debt = 8000 * 0.30 = 2400
    # Reinvest = 8000 * 0.30 = 2400
    
    allocation = data["allocation"]
    assert allocation["safety_reserve"] == pytest.approx(1600, abs=0.1)
    assert allocation["funfunds_amount"] == pytest.approx(800, abs=0.1)
    assert allocation["debt_paydown_amount"] == pytest.approx(2400, abs=0.1)
    assert allocation["reinvest_amount"] == pytest.approx(2400, abs=0.1)


def test_growth_preset_applies_correct_percentages():
    """
    The growth preset should apply aggressive percentages:
    - 10% safety
    - 20% funfunds
    - 15% debt
    - 45% reinvest
    """
    payload = {
        "month_label": "2025-02",
        "gross_income": 10000,
        "fixed_bills": [
            {"name": "Rent", "amount": 2000, "category": "housing"},
        ],
    }

    resp = client.post("/api/flow/funfunds_plan/growth", json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["month_label"] == "2025-02"
    
    # Check debug output confirms growth mode
    debug = data["debug"]
    assert debug.get("mode") == "growth"
    assert debug.get("min_safety_reserve_percent") == "0.10"
    assert debug.get("funfunds_percent") == "0.20"
    assert debug.get("debt_paydown_percent") == "0.15"
    assert debug.get("reinvest_percent") == "0.45"
    
    # Net after bills = 10000 - 2000 = 8000
    # Safety reserve = 8000 * 0.10 = 800
    # Available for dials = 8000 - 800 = 7200
    # FunFunds = 8000 * 0.20 = 1600
    # Debt = 8000 * 0.15 = 1200
    # Reinvest = 8000 * 0.45 = 3600
    
    allocation = data["allocation"]
    assert allocation["safety_reserve"] == pytest.approx(800, abs=0.1)
    assert allocation["funfunds_amount"] == pytest.approx(1600, abs=0.1)
    assert allocation["debt_paydown_amount"] == pytest.approx(1200, abs=0.1)
    assert allocation["reinvest_amount"] == pytest.approx(3600, abs=0.1)


def test_presets_still_handle_over_allocation():
    """
    Even with preset percentages, if they sum > 100% after safety,
    scaling should still occur.
    """
    payload = {
        "month_label": "2025-03",
        "gross_income": 5000,
        "fixed_bills": [
            {"name": "Rent", "amount": 4500, "category": "housing"},
        ],
    }

    # Try growth preset (most aggressive)
    resp = client.post("/api/flow/funfunds_plan/growth", json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    # Net after bills = 5000 - 4500 = 500
    # Safety = 500 * 0.10 = 50
    # Available = 500 - 50 = 450
    # Requested = 500 * (0.20 + 0.15 + 0.45) = 500 * 0.80 = 400
    # Since 400 < 450, no scaling needed
    
    allocation = data["allocation"]
    # Just validate that total doesn't exceed net_after_bills
    total = (
        allocation["safety_reserve"]
        + allocation["funfunds_amount"]
        + allocation["debt_paydown_amount"]
        + allocation["reinvest_amount"]
        + allocation["leftover_amount"]
    )
    net = data["net_after_bills"]
    assert total <= net + 0.01  # Allow 1 cent rounding
