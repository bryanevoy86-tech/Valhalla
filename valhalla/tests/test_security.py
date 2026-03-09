from fastapi.testclient import TestClient
from services.api.main import app as real_app

client = TestClient(real_app)


def test_security_generate_2fa():
    r = client.post("/api/security/generate-2fa", params={"user_id": "user_123"})
    assert r.status_code == 200
    data = r.json()
    assert "user_id" in data and "token_expiry" in data


def test_security_verify_2fa():
    r = client.post("/api/security/verify-2fa", params={"user_id": "user_123", "token": "123456"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("verified") in (True, False)


def test_security_rate_limit():
    r = client.get("/api/security/rate-limit", params={"user_id": "user_123"})
    assert r.status_code == 200
    data = r.json()
    assert "request_count" in data and "reset_time" in data
