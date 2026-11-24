from datetime import datetime, timedelta, timezone
import hashlib
import json
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest
from sqlalchemy.orm import Session

from app.models.completion_registry import LegacyInstanceRegistryItem, LegacyOrchestrationEvent
from app.models.go_live_state import GoLiveState
from app.models.system_metadata import SystemMetadata
from app.services.release_preview import Acceptance, requirements, signature_message


@pytest.mark.parametrize("deal_client", ["disk"], indirect=True)
def test_signed_commissioning_preview_remains_held_for_live_effects(deal_client, monkeypatch):
    client, engine = deal_client
    owner = {"X-Owner-Mandate-Key": "comm-preview-owner-fixture"}
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    signer = Ed25519PrivateKey.generate()
    monkeypatch.setenv("VALHALLA_COMMISSIONING_OBSERVER_PUBLIC_KEY", signer.public_key().public_bytes_raw().hex())
    scope = {"legacy_instance_id": "commission-fixture", "business_id": "pilot-fixture",
             "engine_id": "pilot-engine", "jurisdiction": "CA-MB"}
    for model in (LegacyInstanceRegistryItem, LegacyOrchestrationEvent, GoLiveState, SystemMetadata):
        model.__table__.create(engine, checkfirst=True)
    with Session(engine) as db:
        db.add(LegacyInstanceRegistryItem(
            legacy_instance_id=scope["legacy_instance_id"], display_name="Commissioning fixture",
            assigned_businesses_json=json.dumps([scope["business_id"]]),
            assigned_jurisdictions_json=json.dumps([scope["jurisdiction"]]), engines_json=json.dumps([scope["engine_id"]]),
            local_knowledge_context_json=json.dumps({**scope, "data_namespace": "commission/fixture"}),
            synchronization_status="SYNCED", isolation_state="ISOLATED", failover_state="NOT_TRIGGERED", status="PARTIAL",
        ))
        db.add(GoLiveState(id=1, go_live_enabled=True, kill_switch_engaged=False))
        db.commit()
    now = datetime.now(timezone.utc)
    channel = "commerce_and_fulfillment"
    preview = {"scope": scope, "evidence_id": str(uuid4()), "channel": channel, "authority_sha256": "a" * 64}
    record = {**preview, "basis": "DISPOSABLE_FIXTURE", "observed_at": now.isoformat(),
              "expires_at": (now+timedelta(minutes=5)).isoformat(),
              "requirements": {name: hashlib.sha256(name.encode()).hexdigest() for name in requirements(channel)},
              "signature": "0" * 128}
    record["signature"] = signer.sign(signature_message(Acceptance.model_validate(record))).hex()
    root = "/governance/go-live"
    assert client.post(root + "/commissioning-preview", headers=owner, json=preview).status_code == 409
    assert client.post(root + "/commissioning-evidence", json=record).status_code == 401
    altered = {**record, "authority_sha256": "b" * 64}
    assert client.post(root + "/commissioning-evidence", headers=owner, json=altered).status_code == 409
    stale = {**record, "observed_at": (now - timedelta(hours=2)).isoformat(),
             "expires_at": (now - timedelta(hours=1)).isoformat()}
    stale["signature"] = signer.sign(signature_message(Acceptance.model_validate(stale))).hex()
    assert client.post(root + "/commissioning-evidence", headers=owner, json=stale).status_code == 409
    receipt = client.post(root + "/commissioning-evidence", headers=owner, json=record)
    assert receipt.status_code == 200, receipt.text
    assert client.post(root + "/commissioning-evidence", headers=owner, json=record).json() == receipt.json()
    engine.dispose()
    response = client.post(root + "/commissioning-preview", headers=owner, json=preview)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "READY_FOR_OWNER_SCOPE_REVIEW" and result["commercial_release"] is False
    assert result["standing_mandate_verified"] is False
    assert client.post(root + "/commissioning-preview", headers=owner, json={
        **preview, "channel": "agreements_and_signatures",
    }).status_code == 409
    assert client.post(root + "/commissioning-preview", headers=owner, json={
        **preview, "authority_sha256": "b" * 64,
    }).status_code == 409
    stopped = client.post(root + "/kill-switch/engage", headers=owner, json={"changed_by": "fixture"})
    assert stopped.status_code == 200
    assert client.post(root + "/commissioning-preview", headers=owner, json=preview).json()["status"] == "HELD"
    assert client.post(root + "/enable", headers=owner, json={"changed_by": "fixture"}).status_code == 412
