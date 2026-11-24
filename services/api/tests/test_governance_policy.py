from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

@pytest.fixture
def client(monkeypatch):
    from app.routers.governance_king import KING_POLICY
    monkeypatch.setattr(KING_POLICY, "__dict__", KING_POLICY.model_copy(deep=True).__dict__)
    monkeypatch.setenv("VALHALLA_PRIME_CONTROL_KEY", "isolated-policy-test-prime")
    return TestClient(app, headers={"X-Prime-Control-Key": "isolated-policy-test-prime"})


def test_get_all_policies(client):
    resp = client.get("/api/governance/policies")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    # Ensure all gods are present
    assert "king" in data
    assert "queen" in data
    assert "odin" in data
    assert "loki" in data
    assert "tyr" in data

    # Basic sanity: king has risk section, queen has energy, etc.
    assert "risk" in data["king"]
    assert "energy" in data["queen"]


def test_get_single_policy(client):
    resp = client.get("/api/governance/policies/king")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert "risk" in data
    assert "mission" in data
    assert "values" in data


def test_patch_policy_for_king(client):
    """
    Adjust king risk tolerance, ensure it takes effect.
    """
    # Get current policy
    resp_before = client.get("/api/governance/policies/king")
    assert resp_before.status_code == 200, resp_before.text
    before = resp_before.json()
    old_min_roi = before["risk"]["min_expected_roi"]

    # Patch to a new value
    patch_payload = {
        "risk": {
            "min_expected_roi": "0.20",  # Send as string, Decimal will parse it
        }
    }
    assert client.patch("/api/governance/policies/king", json=patch_payload, headers={"X-Prime-Control-Key": "wrong"}).status_code == 401
    resp_patch = client.patch("/api/governance/policies/king", json=patch_payload)
    assert resp_patch.status_code == 200, resp_patch.text
    patched = resp_patch.json()

    # Pydantic serializes Decimals as strings in JSON
    assert patched["risk"]["min_expected_roi"] == "0.20"

    # Confirm via GET again
    resp_after = client.get("/api/governance/policies/king")
    assert resp_after.status_code == 200, resp_after.text
    after = resp_after.json()

    assert after["risk"]["min_expected_roi"] == "0.20"
    # Should differ from old value as long as old != new
    if old_min_roi != "0.20":
        assert after["risk"]["min_expected_roi"] != old_min_roi


def test_patch_rejects_invalid_data(client):
    """
    Send clearly invalid patch and ensure we get 422.
    """
    patch_payload = {
        "risk": {
            "max_allowed_investment": "not-a-number",
        }
    }
    resp = client.patch("/api/governance/policies/king", json=patch_payload)
    assert resp.status_code == 422
