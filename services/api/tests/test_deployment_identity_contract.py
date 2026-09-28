from fastapi.testclient import TestClient

from app.main import app


def test_deployment_marker_uses_env_commit(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "de6455589e249c8d58f79056f5e197d59c89acbc")

    client = TestClient(app)
    response = client.get("/deployment-marker")
    assert response.status_code == 200

    body = response.json()
    assert body["commit"] == "de6455589e249c8d58f79056f5e197d59c89acbc"
    assert body["commit_short"] == "de64555"
    assert body["commit_source"] == "env"
    assert body["message"] == "Deployment identity from env"


def test_admin_build_info_exposes_runtime_commit_fields(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "de6455589e249c8d58f79056f5e197d59c89acbc")

    client = TestClient(app)
    response = client.get("/admin/build/info")
    assert response.status_code == 200

    body = response.json()
    assert body["git_sha"] == "de6455589e249c8d58f79056f5e197d59c89acbc"
    assert body["git_sha_short"] == "de64555"
    assert body["git_sha_source"] == "env"
    assert "observed_at" in body
