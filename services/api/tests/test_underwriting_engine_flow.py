# services/api/tests/test_underwriting_engine_flow.py

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

# Adjust this import if your app is exposed differently
from main import app  # FastAPI instance


client = TestClient(app)


def test_underwrite_deal_basic_pass_case():
    """
    Happy path:
    - LTV under max
    - ROI above min
    - Equity percent above min
    → recommendation should be 'offer'
    → no freeze_event_created
    """

    payload = {
        "deal": {
            "deal_id": None,
            "org_id": 1,
            "arv": 325000,
            "purchase_price": 230000,   # comfortably below ARV
            "repairs": 40000,
            "closing_costs": 8000,
            "holding_months": 6,
            "monthly_taxes": 300,
            "monthly_insurance": 150,
            "monthly_utilities": 200,
            "monthly_hoa": 0,
            "monthly_other": 100,
            "expected_rent": 2200,
        },
        # Use default policy for now
        "policy": None,
    }

    response = client.post("/api/flow/underwrite_deal", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert "result" in data
    assert "deal_id" in data
    assert "org_id" in data
    assert "freeze_event_created" in data

    result = data["result"]
    metrics = result["metrics"]
    flags = result["flags"]

    # Basic sanity checks on metrics
    assert metrics["total_project_cost"] > 0
    assert metrics["holding_cost_total"] > 0
    assert metrics["ltv"] > 0
    assert metrics["roi"] > 0

    # In a pass case, no breaches expected
    assert flags["breach_ltv"] is False
    assert flags["breach_roi"] is False
    assert flags["breach_equity"] is False
    assert data["freeze_event_created"] is False
    assert result["recommendation"] == "offer"

    print(f"✅ Pass case validated: LTV={metrics['ltv']}, ROI={metrics['roi']}, "
          f"Equity%={metrics['equity_percent_of_arv']}, Recommendation={result['recommendation']}")


def test_underwrite_deal_violation_triggers_freeze():
    """
    Failure path:
    - LTV too high
    - ROI too low
    - Equity percent too low
    → recommendation should be 'reject' or 'renegotiate'
    → freeze_event_created should be True
    """

    # Deliberately bad numbers: purchase near or above ARV, high costs
    payload = {
        "deal": {
            "deal_id": None,
            "org_id": 1,
            "arv": 300000,
            "purchase_price": 290000,  # very high LTV
            "repairs": 40000,
            "closing_costs": 10000,
            "holding_months": 12,
            "monthly_taxes": 400,
            "monthly_insurance": 200,
            "monthly_utilities": 250,
            "monthly_hoa": 150,
            "monthly_other": 200,
            "expected_rent": 1500,
        },
        "policy": None,
    }

    response = client.post("/api/flow/underwrite_deal", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    result = data["result"]
    metrics = result["metrics"]
    flags = result["flags"]

    # Metrics still should be present and valid
    assert metrics["total_project_cost"] > 0
    assert metrics["ltv"] >= 0
    assert metrics["roi"] <= 1

    # With these numbers, we expect at least one breach
    assert (
        flags["breach_ltv"]
        or flags["breach_roi"]
        or flags["breach_equity"]
    ), "Expected at least one policy breach with bad numbers."

    # A policy breach should trigger a freeze event in production DB.
    # In dev / SQLite this might not actually write to DB, but the flag should be True.
    assert data["freeze_event_created"] is True
    assert result["recommendation"] in {"renegotiate", "reject"}

    print(f"✅ Violation case validated: LTV={metrics['ltv']}, ROI={metrics['roi']}, "
          f"Equity%={metrics['equity_percent_of_arv']}, Recommendation={result['recommendation']}, "
          f"Freeze event created: {data['freeze_event_created']}")
    print(f"   Policy violations: {flags['notes']}")


def test_underwrite_deal_custom_policy():
    """
    Test with custom policy override.
    Use stricter thresholds to ensure a marginal deal gets flagged.
    """

    payload = {
        "deal": {
            "deal_id": None,
            "org_id": 1,
            "arv": 320000,
            "purchase_price": 250000,
            "repairs": 35000,
            "closing_costs": 7000,
            "holding_months": 6,
            "monthly_taxes": 250,
            "monthly_insurance": 125,
            "monthly_utilities": 175,
            "monthly_hoa": 0,
            "monthly_other": 75,
            "expected_rent": 2000,
        },
        "policy": {
            "max_ltv": 0.70,      # Stricter: 70% instead of default 80%
            "min_roi": 0.18,      # Stricter: 18% instead of default 12%
            "min_equity_percent": 0.15,  # Stricter: 15% instead of default 10%
            "strategy": "brrrr"
        },
    }

    response = client.post("/api/flow/underwrite_deal", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    result = data["result"]
    metrics = result["metrics"]
    flags = result["flags"]
    policy = result["policy"]

    # Verify custom policy was applied
    assert policy["max_ltv"] == "0.70"
    assert policy["min_roi"] == "0.18"
    assert policy["min_equity_percent"] == "0.15"
    assert policy["strategy"] == "brrrr"

    # With stricter policy, this deal should likely breach
    # (purchase_price 250k on 320k ARV = 78% LTV, exceeds 70%)
    assert flags["breach_ltv"] is True, "Expected LTV breach with 70% max threshold"

    # Should trigger freeze event
    assert data["freeze_event_created"] is True
    assert result["recommendation"] in {"renegotiate", "reject"}

    print(f"✅ Custom policy case validated: Custom max_ltv=0.70 triggered breach")
    print(f"   LTV={metrics['ltv']}, ROI={metrics['roi']}, "
          f"Equity%={metrics['equity_percent_of_arv']}")
    print(f"   Recommendation={result['recommendation']}")


def test_underwrite_deal_brrrr_with_rent_coverage():
    """
    Test BRRRR strategy with rent coverage ratio calculation.
    Ensure rent_coverage_ratio is calculated when expected_rent is provided.
    """

    payload = {
        "deal": {
            "deal_id": None,
            "org_id": 1,
            "arv": 350000,
            "purchase_price": 240000,
            "repairs": 45000,
            "closing_costs": 9000,
            "holding_months": 6,
            "monthly_taxes": 350,
            "monthly_insurance": 175,
            "monthly_utilities": 0,  # No utilities after tenant moves in
            "monthly_hoa": 0,
            "monthly_other": 100,
            "expected_rent": 2500,  # Good rent for this price point
        },
        "policy": {
            "strategy": "brrrr"
        },
    }

    response = client.post("/api/flow/underwrite_deal", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    result = data["result"]
    metrics = result["metrics"]

    # Rent coverage ratio should be calculated
    assert metrics["rent_coverage_ratio"] is not None
    assert float(metrics["rent_coverage_ratio"]) > 0

    # Expected: (2500 * 12) / ((350 + 175 + 100) * 12) = 30000 / 7500 = 4.0
    # Should be around 4.0 or close
    rent_coverage = float(metrics["rent_coverage_ratio"])
    assert rent_coverage > 3.5, f"Expected rent coverage > 3.5, got {rent_coverage}"

    print(f"✅ BRRRR case validated: Rent coverage ratio={metrics['rent_coverage_ratio']}")
    print(f"   Monthly rent=$2500 vs monthly costs=$625 = {rent_coverage:.2f}x coverage")
    print(f"   Recommendation={result['recommendation']}")


if __name__ == "__main__":
    print("Running underwriting engine flow tests...\n")
    test_underwrite_deal_basic_pass_case()
    test_underwrite_deal_violation_triggers_freeze()
    test_underwrite_deal_custom_policy()
    test_underwrite_deal_brrrr_with_rent_coverage()
    print("\n✅ All underwriting engine tests passed!")
