from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import HTTPException
import pytest
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.completion_registry import LegacyOrchestrationEvent
from app.pantheon import identity
from app.pantheon.monitor import run_scheduled_assignment


def test_worker_identity_is_exact_single_use_and_revocable_across_sessions(monkeypatch):
    engine = create_engine("sqlite://")
    LegacyOrchestrationEvent.__table__.create(engine)
    at = datetime(2026, 11, 24, 18)
    monkeypatch.setattr(identity, "now", lambda: at)
    registrar = Ed25519PrivateKey.generate()
    monkeypatch.setenv("VALHALLA_PANTHEON_ENROLLMENT_PRIVATE_KEY", registrar.private_bytes_raw().hex())
    monkeypatch.setenv("VALHALLA_PANTHEON_ENROLLMENT_PUBLIC_KEY", registrar.public_key().public_bytes_raw().hex())
    key = Ed25519PrivateKey.generate()
    other_key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes_raw().hex()
    assignment = SimpleNamespace(id=uuid4(), scope={"legacy_instance_id": "legacy-a", "business_id": "business-a",
        "engine_id": "engine-a", "jurisdiction": "CA-MB"}, role="ODIN", state="active",
        expires_at=at + timedelta(hours=1))
    with Session(engine) as db:
        record = identity.enroll(db, assignment, public, at + timedelta(minutes=10))
        db.commit()
    signer = record["identity_id"]
    monkeypatch.delenv("VALHALLA_PANTHEON_ENROLLMENT_PRIVATE_KEY")
    report = {"report_event_id": "GOD-test", "assignment_id": str(assignment.id), "scope": assignment.scope,
              "role": assignment.role, "worker_identity_id": signer, "execution_path": "SCHEDULED_ROLE_WORKER",
              "observed_at": at.replace(tzinfo=timezone.utc).isoformat(), "status": "observed",
              "observations": {"sample_count": 2}}
    signed = {**report, "worker_signature": key.sign(identity.message(report)).hex()}
    with Session(engine) as db:
        assert identity.verify_signature(db, signed, current=True)["identity_id"] == signer
        for modified in (
            {**signed, "worker_signature": other_key.sign(identity.message(report)).hex()},
            {**signed, "scope": {**assignment.scope, "business_id": "business-b"}},
            {**signed, "observations": {"sample_count": 3}},
            {**signed, "role": "NJORD"},
            {**signed, "assignment_id": str(uuid4())},
        ):
            with pytest.raises(HTTPException) as denied:
                identity.verify_signature(db, modified, current=True)
            assert denied.value.status_code == 409
        with pytest.raises(HTTPException, match="not enrolled"):
            run_scheduled_assignment(db, "ODIN", signing_key=other_key)
        with pytest.raises(HTTPException, match="not enrolled for this role"):
            run_scheduled_assignment(db, "NJORD", signing_key=key)
        with monkeypatch.context() as expired:
            expired.setattr(identity, "now", lambda: at + timedelta(minutes=10))
            with pytest.raises(HTTPException, match="lifetime"):
                identity.verify_signature(db, signed, current=True)
        assert identity.revoke(db, signer)["state"] == "revoked"
        db.commit()
    with Session(engine) as db:
        assert identity.verify_signature(db, signed)["identity_id"] == signer
        with pytest.raises(HTTPException, match="revoked"):
            identity.verify_signature(db, signed, current=True)

        enrollment = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=f"GID-{signer}"))
        body = json.loads(enrollment.payload_json)
        del body["sha256"]
        body["authority_signature"] = "00" * 64
        body["sha256"] = identity.artifact_digest(identity.KIND, enrollment.event_id, body)
        enrollment.payload_json = json.dumps(body)
        db.commit()
        with pytest.raises(HTTPException, match="owner-authority signature"):
            identity.verify_signature(db, signed)
