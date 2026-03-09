from fastapi.testclient import TestClient
from valhalla.services.api.main import app

client = TestClient(app)

def test_healthz():
    r = client.get("/api/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
