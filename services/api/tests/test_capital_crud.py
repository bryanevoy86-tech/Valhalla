from fastapi.testclient import TestClient
from valhalla.services.api.main import app

client = TestClient(app)


def test_record_and_list_intake():
    payload = {"source": "wholesaling", "amount": "1000.00", "currency": "CAD", "note": "initial"}
    r = client.post("/api/capital/intake", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["source"] == payload["source"]
    assert "id" in data

    r2 = client.get("/api/capital/intake")
    assert r2.status_code == 200
    items = r2.json()
    assert any(it["id"] == data["id"] for it in items)
