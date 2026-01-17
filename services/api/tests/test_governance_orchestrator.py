# services/api/tests/test_governance_orchestrator.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_governance_evaluate_all_allows_clean_plan():
    """
    Clean, reasonable plan. All gods should either approve or warn, but
    no hard blocks, so overall_allowed should be True.
    """
    payload = {
        "context_type": "deal",
        "data": {
            # King-ish
            "purchase_price": "200000",
            "repairs": "20000",
            "arv": "300000",
            "roi": "0.20",
            "predatory": "False",

            # Queen-ish
            "hours_per_week": "35",
            "parallel_projects": "2",
            "uses_evenings": "False",
            "uses_weekends": "False",
            "sprint_weeks": "3",
            "stress_level": "5",
            "chaos_factor": "3.0",

            # Odin-ish
            "active_verticals": "2",
            "new_verticals": "0",
            "estimated_annual_profit": "200000",
            "complexity_score": "5",
            "time_to_break_even_months": "12",
            "mission_critical": "True",
            "distraction_score": "2",

            # Loki-ish
            "capital_at_risk": "80000",
            "worst_case_loss": "60000",
            "probability_of_ruin": "0.02",
            "correlation_with_portfolio": "0.5",
            "hidden_complexity_score": "4",

            # Tyr-ish
            "requires_license_without_having_it": "False",
            "tax_evasion": "False",
            "fraudulent_misrepresentation": "False",
            "recording_without_consent": "False",
            "exploits_vulnerable": "False",
            "misleading_marketing": "False",
            "missing_disclosures": "False",
        },
        "gods": None,
    }

    resp = client.post("/api/governance/evaluate_all", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["overall_allowed"] is True
    assert data["worst_severity"] in ["info", "warn"]
    assert isinstance(data["checks"], list)
    assert len(data["checks"]) == 5  # all five gods


def test_governance_evaluate_all_denies_when_tyr_blocks():
    """
    If Tyr sees a red-line violation, overall_allowed should be False.
    """
    payload = {
        "context_type": "deal",
        "data": {
            # Reasonable numbers for others...
            "purchase_price": "200000",
            "repairs": "20000",
            "arv": "300000",
            "roi": "0.20",
            "predatory": "False",

            "hours_per_week": "40",
            "parallel_projects": "2",
            "uses_evenings": "False",
            "uses_weekends": "False",
            "sprint_weeks": "3",
            "stress_level": "6",
            "chaos_factor": "4.0",

            "active_verticals": "2",
            "new_verticals": "0",
            "estimated_annual_profit": "200000",
            "complexity_score": "5",
            "time_to_break_even_months": "12",
            "mission_critical": "True",
            "distraction_score": "2",

            "capital_at_risk": "80000",
            "worst_case_loss": "60000",
            "probability_of_ruin": "0.02",
            "correlation_with_portfolio": "0.5",
            "hidden_complexity_score": "4",

            # Tyr red lines
            "requires_license_without_having_it": "False",
            "tax_evasion": "True",
            "fraudulent_misrepresentation": "False",
            "recording_without_consent": "False",
            "exploits_vulnerable": "False",
            "misleading_marketing": "False",
            "missing_disclosures": "False",
        },
        "gods": ["king", "odin", "tyr"],  # restricted to subset
    }

    resp = client.post("/api/governance/evaluate_all", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["overall_allowed"] is False
    assert data["worst_severity"] == "critical"
    assert "tyr" in data["blocked_by"]
    assert any(ch["god"] == "tyr" for ch in data["checks"])


def test_governance_evaluate_all_subset_of_gods():
    """
    When gods list is specified, only evaluate those gods.
    """
    payload = {
        "context_type": "new_vertical",
        "data": {
            "active_verticals": "3",
            "new_verticals": "1",
            "estimated_annual_profit": "150000",
            "complexity_score": "7",
            "time_to_break_even_months": "18",
            "mission_critical": "False",
            "distraction_score": "6",
        },
        "gods": ["odin"],  # only check Odin
    }

    resp = client.post("/api/governance/evaluate_all", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Should have exactly 1 check (only Odin)
    assert len(data["checks"]) == 1
    assert data["checks"][0]["god"] == "odin"
