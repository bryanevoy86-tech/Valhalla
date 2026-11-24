import pytest


@pytest.mark.integration
def test_health_live(loopback_api):
    response = loopback_api.get("/healthz")
    assert response.status_code == 200, response.text
    assert response.json()["ok"] is True
