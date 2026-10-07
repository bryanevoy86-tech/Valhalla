from __future__ import annotations

from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.notify import test_email_router as notify_router
from app.core.db import get_db
from app.main import app as production_app
from app.routers.test_email import router as email_wiring_router


def _fake_db() -> Iterator[object]:
    # Endpoint only forwards the db session into monkeypatched handlers.
    yield object()


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = FastAPI()
    # Mount production wiring router to keep canonical + compatibility routes.
    app.include_router(email_wiring_router)
    tc = TestClient(app)
    try:
        yield tc
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def _mock_system_identity(monkeypatch):
    monkeypatch.setattr(notify_router, "system_identity", lambda: {"email": "owner@example.com"})


def test_daily_ops_routes_registered_in_openapi(client):
    paths = client.app.openapi().get("paths", {})

    assert "/notify/daily-ops-email" in paths
    assert "post" in paths["/notify/daily-ops-email"]

    assert "/api/notify/daily-ops-email" in paths
    assert "post" in paths["/api/notify/daily-ops-email"]

    assert "/notify/daily-ops-email/health" in paths
    assert "get" in paths["/notify/daily-ops-email/health"]

    assert "/api/notify/daily-ops-email/health" in paths
    assert "get" in paths["/api/notify/daily-ops-email/health"]


def test_daily_ops_route_present_in_production_app_openapi():
    paths = production_app.openapi().get("paths", {})

    assert "/api/notify/daily-ops-email" in paths
    assert "post" in paths["/api/notify/daily-ops-email"]


def test_daily_ops_accepts_post_on_api_prefix(client, monkeypatch):
    monkeypatch.delenv("VALHALLA_CRON_TOKEN", raising=False)
    monkeypatch.setattr(
        notify_router,
        "dispatch_daily_ops_email",
        lambda db, source: {
            "ok": True,
            "status": "sent",
            "sent_to": "owner@example.com",
            "subject": "Heimdall: Daily Ops (9AM)",
            "idempotency_key": "k",
            "attempt_count": 1,
            "skipped": False,
        },
    )
    client.app.dependency_overrides[get_db] = _fake_db

    try:
        res = client.post("/api/notify/daily-ops-email")
        assert res.status_code == 200
        payload = res.json()
        assert payload["ok"] is True
        assert payload["sent_to"] == "owner@example.com"
    finally:
        client.app.dependency_overrides.pop(get_db, None)


def test_daily_ops_get_method_is_rejected(client):
    res = client.get("/api/notify/daily-ops-email")
    assert res.status_code == 405


def test_daily_ops_requires_cron_token_when_configured(client, monkeypatch):
    monkeypatch.setenv("VALHALLA_CRON_TOKEN", "secret-token")
    monkeypatch.setattr(
        notify_router,
        "dispatch_daily_ops_email",
        lambda db, source: {
            "ok": True,
            "status": "sent",
            "sent_to": "owner@example.com",
            "subject": "Heimdall: Daily Ops (9AM)",
            "idempotency_key": "k",
            "attempt_count": 1,
            "skipped": False,
        },
    )
    client.app.dependency_overrides[get_db] = _fake_db

    try:
        missing = client.post("/api/notify/daily-ops-email")
        assert missing.status_code == 403

        wrong = client.post(
            "/api/notify/daily-ops-email",
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert wrong.status_code == 403

        ok = client.post(
            "/api/notify/daily-ops-email",
            headers={"Authorization": "Bearer secret-token"},
        )
        assert ok.status_code == 200
    finally:
        client.app.dependency_overrides.pop(get_db, None)


def test_daily_ops_provider_failure_is_visible(client, monkeypatch):
    monkeypatch.delenv("VALHALLA_CRON_TOKEN", raising=False)

    def _boom(db, source):
        raise RuntimeError("Daily ops email send failed")

    monkeypatch.setattr(notify_router, "dispatch_daily_ops_email", _boom)
    client.app.dependency_overrides[get_db] = _fake_db

    try:
        res = client.post("/api/notify/daily-ops-email")
        assert res.status_code == 503
        assert "send failed" in res.json().get("detail", "").lower()
    finally:
        client.app.dependency_overrides.pop(get_db, None)


def test_daily_ops_unknown_prior_result_is_blocked(client, monkeypatch):
    monkeypatch.delenv("VALHALLA_CRON_TOKEN", raising=False)

    def _blocked(db, source):
        raise RuntimeError("Daily ops email retry blocked due to unknown previous provider result")

    monkeypatch.setattr(notify_router, "dispatch_daily_ops_email", _blocked)
    client.app.dependency_overrides[get_db] = _fake_db

    try:
        res = client.post("/api/notify/daily-ops-email")
        assert res.status_code == 503
        assert "unknown previous provider result" in res.json().get("detail", "").lower()
    finally:
        client.app.dependency_overrides.pop(get_db, None)


def test_daily_ops_duplicate_calls_are_idempotent(client, monkeypatch):
    monkeypatch.delenv("VALHALLA_CRON_TOKEN", raising=False)

    calls = {"n": 0}

    def _dispatch(db, source):
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "ok": True,
                "status": "sent",
                "sent_to": "owner@example.com",
                "subject": "Heimdall: Daily Ops (9AM)",
                "idempotency_key": "k",
                "attempt_count": 1,
                "skipped": False,
            }
        return {
            "ok": True,
            "status": "duplicate_skipped",
            "sent_to": "owner@example.com",
            "subject": "Heimdall: Daily Ops (9AM)",
            "idempotency_key": "k",
            "attempt_count": 2,
            "skipped": True,
        }

    monkeypatch.setattr(notify_router, "dispatch_daily_ops_email", _dispatch)
    client.app.dependency_overrides[get_db] = _fake_db

    try:
        first = client.post("/api/notify/daily-ops-email")
        second = client.post("/api/notify/daily-ops-email")
        assert first.status_code == 200
        assert second.status_code == 200

        first_json = first.json()
        second_json = second.json()

        assert first_json["status"] == "sent"
        assert second_json["status"] == "duplicate_skipped"
        assert first_json["idempotency_key"] == second_json["idempotency_key"]
        assert calls["n"] == 2
    finally:
        client.app.dependency_overrides.pop(get_db, None)


def test_daily_ops_health_endpoint_reports_fields(client, monkeypatch):
    monkeypatch.setattr(
        notify_router,
        "get_daily_email_health_status",
        lambda db: {
            "status": "GREEN",
            "duplicate_send_protection_state": "ENABLED_STRICT",
            "last_attempt_at": "2026-01-01T00:00:00+00:00",
            "last_success_at": "2026-01-01T00:00:00+00:00",
            "last_failure_at": None,
            "last_result": {"status": "sent"},
            "owner_timezone": "UTC",
            "schedule": "0 9 * * *",
            "next_scheduled_run_utc": "2026-01-02T09:00:00+00:00",
        },
    )
    client.app.dependency_overrides[get_db] = _fake_db

    try:
        health_res = client.get("/api/notify/daily-ops-email/health")
        assert health_res.status_code == 200
        payload = health_res.json()

        assert payload["duplicate_send_protection_state"] == "ENABLED_STRICT"
        assert payload["status"] in {"GREEN", "DEGRADED", "BLOCKED"}
        assert payload["schedule"] == "0 9 * * *"
        assert payload["owner_timezone"]
        assert payload["next_scheduled_run_utc"]
    finally:
        client.app.dependency_overrides.pop(get_db, None)
