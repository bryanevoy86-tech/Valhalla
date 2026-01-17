from fastapi.testclient import TestClient
from valhalla.services.api.main import app

client = TestClient(app)

def test_metrics_crud():
    create = client.post("/api/metrics", json={"name":"fx_monthly_yield","value":5.0,"unit":"%","tags":"engine:fx"})
    assert create.status_code == 200
    data = create.json()
    assert data["name"] == "fx_monthly_yield"
    lst = client.get("/api/metrics")
    assert lst.status_code == 200
    assert any(m["id"] == data["id"] for m in lst.json())
