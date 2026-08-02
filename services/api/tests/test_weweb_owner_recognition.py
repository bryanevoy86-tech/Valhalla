import os
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Minimal auth env bootstrap for importing app.security.auth in test context.
os.environ.setdefault("VALHALLA_OWNER_PASSWORD", "test-owner-pass")
os.environ.setdefault("VALHALLA_JWT_SECRET", "test-jwt-secret")

from app.routers import auth_weweb
from app.security.auth import SETTINGS, jwt_encode, pbkdf2_hash_password
from app.users.models import AccountSettings, UserProfile


@pytest.fixture()
def weweb_client(monkeypatch):
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
        owner = UserProfile(
            first_name="Owner",
            last_name="User",
            email="owner@example.com",
        )
        other = UserProfile(
            first_name="Other",
            last_name="User",
            email="other@example.com",
        )
        db.add_all([owner, other])
        db.flush()

        db.add_all(
            [
                AccountSettings(
                    user_id=owner.user_id,
                    password_hash=pbkdf2_hash_password("OwnerPass!1"),
                ),
                AccountSettings(
                    user_id=other.user_id,
                    password_hash=pbkdf2_hash_password("OtherPass!1"),
                ),
            ]
        )
        db.commit()
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

    app.dependency_overrides[auth_weweb.get_db] = override_get_db

    client = TestClient(app)

    def make_token(email: str, user_id: int, exp_offset_seconds: int = 3600) -> str:
        now = int(time.time())
        payload = {
            "sub": email,
            "user_id": user_id,
            "iat": now,
            "exp": now + exp_offset_seconds,
        }
        return jwt_encode(payload, SETTINGS.jwt_secret)

    return client, make_token


def _get_user_id(client: TestClient, email: str) -> int:
    # Use login to avoid hardcoding IDs and keep fixture resilient.
    resp = client.post(
        "/api/weweb/login",
        json={
            "email": email,
            "password": "OwnerPass!1" if email == "owner@example.com" else "OtherPass!1",
        },
    )
    data = resp.json()
    return data["user"]["id"]


def test_owner_true_for_configured_owner(weweb_client, monkeypatch):
    client, make_token = weweb_client
    monkeypatch.setenv("VALHALLA_OWNER_EMAIL", "owner@example.com")

    owner_id = _get_user_id(client, "owner@example.com")
    token = make_token("owner@example.com", owner_id)

    resp = client.get("/api/weweb/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["is_owner"] is True


def test_owner_false_for_different_user(weweb_client, monkeypatch):
    client, make_token = weweb_client
    monkeypatch.setenv("VALHALLA_OWNER_EMAIL", "owner@example.com")

    other_id = _get_user_id(client, "other@example.com")
    token = make_token("other@example.com", other_id)

    resp = client.get("/api/weweb/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["is_owner"] is False


def test_owner_comparison_is_case_insensitive(weweb_client, monkeypatch):
    client, make_token = weweb_client
    monkeypatch.setenv("VALHALLA_OWNER_EMAIL", "  OWNER@EXAMPLE.COM  ")

    owner_id = _get_user_id(client, "owner@example.com")
    token = make_token("owner@example.com", owner_id)

    resp = client.get("/api/weweb/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["is_owner"] is True


def test_missing_owner_configuration_fails_safe_false(weweb_client, monkeypatch):
    client, make_token = weweb_client
    monkeypatch.delenv("VALHALLA_OWNER_EMAIL", raising=False)

    owner_id = _get_user_id(client, "owner@example.com")
    token = make_token("owner@example.com", owner_id)

    resp = client.get("/api/weweb/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["is_owner"] is False


def test_unauthenticated_request_fails(weweb_client):
    client, _ = weweb_client
    resp = client.get("/api/weweb/me")
    assert resp.status_code == 401


def test_invalid_jwt_fails(weweb_client):
    client, _ = weweb_client
    resp = client.get("/api/weweb/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert resp.status_code == 401


def test_expired_jwt_fails(weweb_client):
    client, make_token = weweb_client
    owner_id = _get_user_id(client, "owner@example.com")
    expired = make_token("owner@example.com", owner_id, exp_offset_seconds=-30)

    resp = client.get("/api/weweb/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


def test_request_data_cannot_grant_owner(weweb_client, monkeypatch):
    client, make_token = weweb_client
    monkeypatch.setenv("VALHALLA_OWNER_EMAIL", "owner@example.com")

    other_id = _get_user_id(client, "other@example.com")
    token = make_token("other@example.com", other_id)

    resp = client.get(
        "/api/weweb/me?is_owner=true&owner=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["is_owner"] is False
