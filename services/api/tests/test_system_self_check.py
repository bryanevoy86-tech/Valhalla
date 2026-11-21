import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.db import get_db
from app.models.audit_log import AuditLog
from app.models.completion_registry import LearningTaskQueueItem
from app.models.go_live_state import GoLiveState
from app.routers.system_self_check import router


def test_private_self_check_reads_real_signals_and_only_post_records_alerts(monkeypatch):
    monkeypatch.setenv("VALHALLA_PRIME_CONTROL_KEY", "isolated-integrity-key")
    monkeypatch.delenv("VALHALLA_EMERGENCY_STOP", raising=False)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for model in (GoLiveState, LearningTaskQueueItem, AuditLog):
        model.__table__.create(engine)
    app = FastAPI()
    app.include_router(router)

    def test_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    headers = {"X-Prime-Control-Key": "isolated-integrity-key"}
    try:
        with TestClient(app) as client:
            path = "/api/system/self-check"
            assert client.get(path).status_code == 401
            assert client.post(path).status_code == 401
            missing = client.get(path, headers=headers).json()
            assert "release_state_missing" in missing["anomaly_detection"]["signals"]

            with Session(engine) as db:
                db.add(GoLiveState(id=1, kill_switch_engaged=False))
                db.commit()
            clear = client.post(path, headers=headers).json()
            assert clear["anomaly_detection"]["state"] == "NO_ANOMALY_IN_CHECKED_SIGNALS"
            assert clear["integrity_audit_trail"]["events_emitted"] == 0

            with Session(engine) as db:
                db.get(GoLiveState, 1).kill_switch_engaged = True
                db.add(LearningTaskQueueItem(
                    task_id="test-1", task_type="REVERIFY_KNOWLEDGE", status="blocked",
                    priority="high", domain="OPERATIONS", reason="Test blocked task",
                ))
                db.commit()
            preview = client.get(f"{path}?probe_isolation_violation=true", headers=headers).json()
            assert preview["integrity_audit_trail"]["events_emitted"] == 0
            assert preview["fail_safe_state"]["active"] is True
            assert set(preview["anomaly_detection"]["signals"]) == {"kill_switch", "learning_queue_blocked"}
            with Session(engine) as db:
                assert db.query(AuditLog).count() == 0

            response = client.post(path, headers=headers)
            assert response.status_code == 200
            assert response.json()["integrity_audit_trail"]["events_emitted"] == 1
            with Session(engine) as db:
                audit = db.query(AuditLog).one()
                assert audit.event_type == "integrity_alert"
                assert json.loads(audit.event_data) == preview["anomaly_detection"]["signals"]

            AuditLog.__table__.drop(engine)
            assert client.post(path, headers=headers).status_code == 503
    finally:
        engine.dispose()
