from fastapi.testclient import TestClient
from valhalla.services.api.main import app


def test_health():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    assert "app" in data and data["app"].startswith("Valhalla")
