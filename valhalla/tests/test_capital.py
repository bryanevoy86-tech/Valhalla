from fastapi.testclient import TestClient
from valhalla.services.api.main import app

client = TestClient(app)

def test_capital_intake():
    create = client.post("/api/capital/intake", json={"source":"wholesaling","amount":"12500.00","currency":"CAD"})
    assert create.status_code == 200
    got = client.get("/api/capital/intake")
    assert got.status_code == 200
    rows = got.json()
    assert any(r["source"] == "wholesaling" for r in rows)
