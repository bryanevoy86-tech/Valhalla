import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import get_db
from app.routers import auth_weweb
from app.users.models import AccountSettings, UserProfile


@pytest.fixture()
def weweb_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("VALHALLA_OWNER_EMAIL", "owner@example.com")
    monkeypatch.setenv("VALHALLA_OWNER_USERNAME", "owner")
    monkeypatch.setenv("VALHALLA_OWNER_PASSWORD", "OwnerPass!1")
    monkeypatch.setenv("VALHALLA_JWT_SECRET", "test-secret")

    # Import after env is set because auth settings are loaded at import time.
    from app.security import auth as auth_runtime

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine)

    UserProfile.__table__.create(bind=engine, checkfirst=True)
    AccountSettings.__table__.create(bind=engine, checkfirst=True)

    db = SessionLocal()
    try:
        owner = UserProfile(first_name="Owner", last_name="User", email="owner@example.com")
        db.add(owner)
        db.flush()
        db.add(
            AccountSettings(
                user_id=owner.user_id,
                password_hash=auth_runtime.pbkdf2_hash_password("OwnerPass!1"),
            )
        )
        db.commit()
        owner_id = owner.user_id
    finally:
        db.close()

    app = FastAPI()
    app.include_router(auth_weweb.router)

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[auth_weweb.get_db] = override_get_db

    return TestClient(app), auth_runtime, owner_id


def _login_token(client: TestClient) -> str:
    resp = client.post(
        "/api/weweb/login",
        json={"email": "owner@example.com", "password": "OwnerPass!1"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_openapi_includes_logout_route(weweb_client):
    client, _, _ = weweb_client
    paths = client.app.openapi().get("paths", {})

    assert "/api/weweb/logout" in paths
    assert "post" in paths["/api/weweb/logout"]


def test_logout_authenticated_revokes_token_and_denies_me(weweb_client):
    client, _, _ = weweb_client
    token = _login_token(client)

    logout = client.post("/api/weweb/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout.status_code == 200
    assert logout.json()["ok"] is True

    me = client.get("/api/weweb/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 401


def test_logout_unauthenticated_is_denied(weweb_client):
    client, _, _ = weweb_client

    logout = client.post("/api/weweb/logout")
    assert logout.status_code == 401


def test_logout_invalid_token_is_denied(weweb_client):
    client, _, _ = weweb_client

    logout = client.post("/api/weweb/logout", headers={"Authorization": "Bearer not-a-jwt"})
    assert logout.status_code == 401


def test_logout_expired_token_is_denied(weweb_client):
    client, auth_runtime, owner_id = weweb_client

    now = int(time.time())
    payload = {
        "sub": "owner@example.com",
        "user_id": owner_id,
        "iat": now - 120,
        "exp": now - 60,
        "jti": "expired-test-jti",
    }
    expired = auth_runtime.jwt_encode(payload, auth_runtime.SETTINGS.jwt_secret)

    logout = client.post("/api/weweb/logout", headers={"Authorization": f"Bearer {expired}"})
    assert logout.status_code == 401
