from app.main import app
from fastapi.testclient import TestClient


def test_live():
    with TestClient(app) as c:
        r = c.get("/api/v1/health/live")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
