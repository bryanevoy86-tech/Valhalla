# services/api/tests/test_governance_tyr.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_tyr_allows_clean_action():
    """
    No legal or ethical flags: Tyr should allow.
    """
    payload = {
        "context_type": "operation",
        "data": {
            "requires_license_without_having_it": "False",
            "tax_evasion": "False",
            "fraudulent_misrepresentation": "False",
            "recording_without_consent": "False",
            "exploits_vulnerable": "False",
            "misleading_marketing": "False",
            "missing_disclosures": "False",
        },
    }
    resp = client.post("/api/governance/tyr/evaluate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is True
    assert data["severity"] == "info"
    assert data["reasons"] == []


def test_tyr_denies_unlicensed_and_tax_evasion():
    """
    Clear legal violations: unlicensed practice + tax evasion. Tyr should deny.
    """
    payload = {
        "context_type": "operation",
        "data": {
            "requires_license_without_having_it": "True",
            "tax_evasion": "True",
            "fraudulent_misrepresentation": "False",
            "recording_without_consent": "False",
            "exploits_vulnerable": "False",
            "misleading_marketing": "False",
            "missing_disclosures": "False",
        },
    }
    resp = client.post("/api/governance/tyr/evaluate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is False
    assert data["severity"] == "critical"
    assert len(data["reasons"]) >= 1


def test_tyr_denies_exploitative_and_misleading_behavior():
    """
    Ethical red lines: exploiting vulnerable + misleading marketing.
    Tyr should deny.
    """
    payload = {
        "context_type": "deal",
        "data": {
            "requires_license_without_having_it": "False",
            "tax_evasion": "False",
            "fraudulent_misrepresentation": "False",
            "recording_without_consent": "False",
            "exploits_vulnerable": "True",
            "misleading_marketing": "True",
            "missing_disclosures": "True",
        },
    }
    resp = client.post("/api/governance/tyr/evaluate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is False
    assert data["severity"] == "critical"
    assert len(data["reasons"]) >= 1
