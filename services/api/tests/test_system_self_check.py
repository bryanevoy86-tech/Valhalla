from __future__ import annotations

import json
import time
from datetime import date, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import get_db
from app.core.runtime_flags import RuntimeMode, set_runtime_mode
from app.models.completion_registry import DatasetRegistryItem, KnowledgeRegistryItem, SourceRegistryItem
from app.models.audit_log import AuditLog
from app.models.owner_command import OwnerCommand
from app.models.pending_action import PendingAction
from app.routers.completion_registry import router as completion_router
from app.routers.system_self_check import router


def _build_client(include_completion_router: bool = False) -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(bind=engine)

    PendingAction.__table__.create(bind=engine, checkfirst=True)
    OwnerCommand.__table__.create(bind=engine, checkfirst=True)
    SourceRegistryItem.__table__.create(bind=engine, checkfirst=True)
    KnowledgeRegistryItem.__table__.create(bind=engine, checkfirst=True)
    DatasetRegistryItem.__table__.create(bind=engine, checkfirst=True)
    AuditLog.__table__.create(bind=engine, checkfirst=True)

    app = FastAPI()
    if include_completion_router:
        app.include_router(completion_router)
    app.include_router(router)

    def override_get_db():
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _components_by_id(body: dict) -> dict:
    rows = body["process_health"]["components"] + body["business_capability_readiness"]["components"]
    return {row["component_id"]: row for row in rows}


def _write_json(path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _configure_weweb_files(tmp_path, monkeypatch, authenticated: bool) -> None:
    mcp_cfg = tmp_path / "mcp.json"
    _write_json(
        mcp_cfg,
        {
            "servers": {
                "weweb-ai": {
                    "type": "http",
                    "url": "https://ai-api.weweb.io/v1/mcp",
                }
            }
        },
    )
    evidence = tmp_path / "weweb_auth.json"
    _write_json(
        evidence,
        {
            "authenticated": authenticated,
            "project_discovered": authenticated,
            "valhalla_project_confirmed": authenticated,
            "read_access_proven": authenticated,
        },
    )
    monkeypatch.setenv("VALHALLA_WEWEB_MCP_CONFIG_PATH", str(mcp_cfg))
    monkeypatch.setenv("VALHALLA_WEWEB_AUTH_EVIDENCE_PATH", str(evidence))


def test_self_check_all_healthy(tmp_path, monkeypatch):
    client = _build_client(include_completion_router=True)

    heartbeat = tmp_path / "heartbeat.json"
    _write_json(heartbeat, {"ts": time.time()})
    monkeypatch.setenv("VALHALLA_WORKER_HEARTBEAT_FILE", str(heartbeat))

    _configure_weweb_files(tmp_path, monkeypatch, authenticated=True)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "ops@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")
    monkeypatch.setenv("VALHALLA_FUTURE_ENGINES_ACTIVE", "")
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "0")

    set_runtime_mode(RuntimeMode.LIVE)

    src = client.post(
        "/api/completion/source-items",
        json={
            "source_id": "SRC-HEALTH-001",
            "canonical_name": "Health Source",
            "source_type": "fixture",
            "data_class": "live",
            "terminal_state": "ACTIVE_AND_VERIFIED",
        },
    )
    assert src.status_code == 200

    know = client.post(
        "/api/completion/knowledge-items",
        json={
            "item_id": "KNOW-HEALTH-001",
            "source": "SRC-HEALTH-001",
            "source_type": "fixture",
            "title": "OPERATIONS healthy policy",
            "terminal_state": "ACTIVE_AND_VERIFIED",
            "review_status": "approved",
            "quality_score": 0.95,
            "confidence_score": 0.95,
            "review_date": date.today().isoformat(),
        },
    )
    assert know.status_code == 200

    response = client.get("/api/system/self-check")
    assert response.status_code == 200
    body = response.json()
    components = _components_by_id(body)

    assert components["database"]["status"] == "GREEN"
    assert components["worker_lease"]["status"] == "GREEN"
    assert components["critical_providers"]["status"] == "GREEN"
    assert components["weweb_connection"]["status"] == "GREEN"
    assert body["process_health"]["status"] == "GREEN"


def test_self_check_worker_stuck(tmp_path, monkeypatch):
    client = _build_client()

    heartbeat = tmp_path / "heartbeat.json"
    _write_json(heartbeat, {"ts": time.time() - 9999})
    monkeypatch.setenv("VALHALLA_WORKER_HEARTBEAT_FILE", str(heartbeat))
    monkeypatch.setenv("VALHALLA_WORKER_HEARTBEAT_MAX_AGE_SECONDS", "30")

    response = client.get("/api/system/self-check")
    assert response.status_code == 200
    components = _components_by_id(response.json())
    assert components["worker_lease"]["status"] == "BLOCKED"


def test_self_check_emergency_stop_active(monkeypatch):
    client = _build_client()
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "1")

    response = client.get("/api/system/self-check")
    assert response.status_code == 200
    components = _components_by_id(response.json())
    assert components["emergency_stop"]["status"] == "CRITICAL"


def test_self_check_provider_missing_blocks(monkeypatch):
    client = _build_client()
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASS", raising=False)
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("TWILIO_PHONE_NUMBER", raising=False)
    monkeypatch.delenv("DOCUSIGN_POWERFORM_URL", raising=False)

    response = client.get("/api/system/self-check")
    assert response.status_code == 200
    components = _components_by_id(response.json())
    assert components["critical_providers"]["status"] == "BLOCKED"


def test_self_check_database_unavailable(monkeypatch):
    client = _build_client()
    from app.services import system_self_check as svc

    monkeypatch.setattr(
        svc,
        "_check_db_health",
        lambda _db: svc._component(
            component_id="database",
            name="Primary Database",
            scope="PROCESS_HEALTH",
            status="CRITICAL",
            evidence="forced db failure",
            impact="db unavailable",
            blocking=True,
            owner_action_required=True,
        ),
    )

    response = client.get("/api/system/self-check")
    assert response.status_code == 200
    components = _components_by_id(response.json())
    assert components["database"]["status"] == "CRITICAL"


def test_self_check_weweb_configured_but_not_authenticated_is_not_green(tmp_path, monkeypatch):
    client = _build_client()
    _configure_weweb_files(tmp_path, monkeypatch, authenticated=False)

    response = client.get("/api/system/self-check")
    assert response.status_code == 200
    comp = _components_by_id(response.json())["weweb_connection"]
    assert comp["status"] == "BLOCKED"
    assert "AUTH_REQUIRED" in " ".join(comp["details"].get("state_chain", []))


def test_self_check_weweb_authenticated_state_is_green(tmp_path, monkeypatch):
    client = _build_client()
    _configure_weweb_files(tmp_path, monkeypatch, authenticated=True)

    response = client.get("/api/system/self-check")
    assert response.status_code == 200
    comp = _components_by_id(response.json())["weweb_connection"]
    assert comp["status"] == "GREEN"


def test_self_check_practice_mode_active_is_not_live_green(monkeypatch):
    client = _build_client()
    set_runtime_mode(RuntimeMode.SANDBOX)

    response = client.get("/api/system/self-check")
    assert response.status_code == 200
    comp = _components_by_id(response.json())["practice_live_mode"]
    assert comp["status"] == "DEGRADED"


def test_self_check_future_engine_incorrectly_enabled(monkeypatch):
    client = _build_client()
    monkeypatch.setenv("VALHALLA_FUTURE_ENGINES_ACTIVE", "trading_advisory")

    response = client.get("/api/system/self-check")
    assert response.status_code == 200
    comp = _components_by_id(response.json())["future_engine_locks"]
    assert comp["status"] == "BLOCKED"


def test_self_check_critical_knowledge_stale(tmp_path, monkeypatch):
    client = _build_client(include_completion_router=True)

    # Configure heartbeat and auth to avoid unrelated hard blockers.
    heartbeat = tmp_path / "heartbeat.json"
    _write_json(heartbeat, {"ts": time.time()})
    monkeypatch.setenv("VALHALLA_WORKER_HEARTBEAT_FILE", str(heartbeat))
    _configure_weweb_files(tmp_path, monkeypatch, authenticated=True)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "ops@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")
    set_runtime_mode(RuntimeMode.LIVE)

    src = client.post(
        "/api/completion/source-items",
        json={
            "source_id": "SRC-STALE-001",
            "canonical_name": "Stale Source",
            "source_type": "fixture",
            "data_class": "live",
            "terminal_state": "ACTIVE_AND_VERIFIED",
        },
    )
    assert src.status_code == 200

    stale_date = (date.today() - timedelta(days=120)).isoformat()
    know = client.post(
        "/api/completion/knowledge-items",
        json={
            "item_id": "KNOW-STALE-001",
            "source": "SRC-STALE-001",
            "source_type": "fixture",
            "title": "OPERATIONS stale policy",
            "terminal_state": "ACTIVE_AND_VERIFIED",
            "review_status": "approved",
            "quality_score": 0.95,
            "confidence_score": 0.95,
            "review_date": stale_date,
        },
    )
    assert know.status_code == 200

    response = client.get("/api/system/self-check")
    assert response.status_code == 200
    comp = _components_by_id(response.json())["knowledge_freshness"]
    assert comp["status"] == "BLOCKED"


def test_self_check_isolation_violation_probe(tmp_path, monkeypatch):
    client = _build_client(include_completion_router=True)

    source = client.post(
        "/api/completion/source-items",
        json={
            "source_id": "SRC-PROBE-001",
            "canonical_name": "Probe Source",
            "source_type": "fixture",
            "data_class": "synthetic",
            "terminal_state": "ACTIVE_AND_VERIFIED",
        },
    )
    assert source.status_code == 200

    dataset = client.post(
        "/api/completion/dataset-items",
        json={
            "dataset_id": "DS-PROBE-SYN-001",
            "name": "Probe Synthetic",
            "type": "SYNTHETIC_OPERATIONAL",
            "purpose": "probe isolation",
            "domain": "OPERATIONS",
            "status": "active",
            "source_id": "SRC-PROBE-001",
            "terminal_state": "ACTIVE_AND_VERIFIED",
        },
    )
    assert dataset.status_code == 200

    heartbeat = tmp_path / "heartbeat.json"
    _write_json(heartbeat, {"ts": time.time()})
    monkeypatch.setenv("VALHALLA_WORKER_HEARTBEAT_FILE", str(heartbeat))
    _configure_weweb_files(tmp_path, monkeypatch, authenticated=True)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "ops@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")

    response = client.get("/api/system/self-check?probe_isolation_violation=true")
    assert response.status_code == 200
    comp = _components_by_id(response.json())["source_isolation"]
    assert comp["status"] == "GREEN"
    assert "blocked as expected" in comp["evidence"].lower()


def test_self_check_reports_reverify_backlog_and_anomaly_state(tmp_path, monkeypatch):
    client = _build_client(include_completion_router=True)

    heartbeat = tmp_path / "heartbeat.json"
    _write_json(heartbeat, {"ts": time.time()})
    monkeypatch.setenv("VALHALLA_WORKER_HEARTBEAT_FILE", str(heartbeat))
    _configure_weweb_files(tmp_path, monkeypatch, authenticated=True)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "ops@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")

    task = client.post(
        "/api/completion/learning/tasks",
        json={
            "task_id": "LQ-REVERIFY-SYSTEM-001",
            "task_type": "REVERIFY_KNOWLEDGE",
            "status": "queued",
            "priority": "critical",
            "domain": "OPERATIONS",
            "reason": "hard stale policy requires re-verification",
        },
    )
    assert task.status_code == 200

    response = client.get("/api/system/self-check")
    assert response.status_code == 200
    body = response.json()
    components = _components_by_id(body)

    assert "learning_reverify_backlog" in components
    assert components["learning_reverify_backlog"]["details"]["open_reverify_tasks"] >= 1
    assert "system_blocker_count" in body
    assert "anomaly_detection" in body


def test_self_check_emits_integrity_alert_audit_when_critical(tmp_path, monkeypatch):
    client = _build_client(include_completion_router=True)

    heartbeat = tmp_path / "heartbeat.json"
    _write_json(heartbeat, {"ts": time.time() - 9999})
    monkeypatch.setenv("VALHALLA_WORKER_HEARTBEAT_FILE", str(heartbeat))
    monkeypatch.setenv("VALHALLA_WORKER_HEARTBEAT_MAX_AGE_SECONDS", "10")
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "1")

    response = client.get("/api/system/self-check")
    assert response.status_code == 200
    body = response.json()
    assert body["fail_safe_state"]["active"] is True
    assert body["integrity_audit_trail"]["events_emitted"] >= 1
