from fastapi.testclient import TestClient
from valhalla.services.api.main import app

client = TestClient(app)


def test_create_and_list_metric():
    payload = {"name": "fx_monthly_yield", "value": 1.23, "unit": "%", "tags": "engine:fx"}
    r = client.post("/api/metrics", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == payload["name"]
    assert "id" in data

    # list
    r2 = client.get("/api/metrics")
    assert r2.status_code == 200
    items = r2.json()
    assert any(it["id"] == data["id"] for it in items)
