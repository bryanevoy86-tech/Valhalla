import base64
import hashlib
import json
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.completion_registry import LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.media_engine import MediaContent
from app.models.product_artifact import ProductArtifact


FACTORY = "/api/business-factory"
ASSETS = f"{FACTORY}/product-artifacts"


def test_internal_product_asset_stage_bind_verify_and_revoke(deal_client, monkeypatch):
    client, engine = deal_client
    admin = {"X-Business-Factory-Key": "ci-factory-for-product-assets"}
    owner = {**admin, "X-Owner-Mandate-Key": "ci-owner-for-product-assets"}
    monkeypatch.setenv("VALHALLA_FACTORY_KEY", admin["X-Business-Factory-Key"])
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    for model in (LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, MediaContent):
        model.__table__.create(engine)

    scope = {"legacy_instance_id": "legacy-north", "business_id": "workshop", "engine_id": "micro_saas", "jurisdiction": "CA-MB"}
    with Session(engine) as db:
        db.add(LegacyInstanceRegistryItem(
            legacy_instance_id=scope["legacy_instance_id"], display_name="Internal operating legacy",
            assigned_businesses_json='["workshop"]', assigned_jurisdictions_json='["CA-MB"]', engines_json='["micro_saas"]',
            local_knowledge_context_json='{"business_id":"workshop","jurisdiction":"CA-MB"}',
            synchronization_status="SYNCED", status="PASS",
        ))
        db.commit()

    content = b"Valhalla owns this product test file.\n"
    checksum = hashlib.sha256(content).hexdigest()
    asset_id = str(uuid4())
    asset = {
        **scope, "artifact_id": asset_id, "product_id": "workshop-guide", "version": 1,
        "media_type": "text/plain", "sha256": checksum,
        "content_base64": base64.b64encode(content).decode(), "rights_reference": "internal-rights-register/example-001",
        "attestation": "OWNER_AUTHORIZES_INTERNAL_STORAGE_AND_USE",
    }

    assert client.post(ASSETS, headers=owner, json=asset).status_code == 503
    ProductArtifact.__table__.create(engine)
    assert client.post(ASSETS, headers=admin, json=asset).status_code == 401
    assert client.post(ASSETS, headers=owner, content=b"x" * (7 * 1024 * 1024 + 1)).status_code == 413
    assert client.post(ASSETS, headers=owner, json={**asset, "sha256": "0" * 64}).status_code == 422
    assert client.post(ASSETS, headers=owner, json={**asset, "media_type": "application/pdf"}).status_code == 422
    assert client.post(ASSETS, headers=owner, json={**asset, "jurisdiction": "CA-ON"}).status_code == 409

    staged = client.post(ASSETS, headers=owner, json=asset)
    assert staged.status_code == 201, staged.text
    assert staged.json()["rights_basis"] == "OWNER_ATTESTED_INTERNAL_USE"
    assert staged.json()["external_delivery_authorized"] is False
    assert client.post(ASSETS, headers=owner, json=asset).json() == staged.json()
    assert client.post(ASSETS, headers=owner, json={**asset, "artifact_id": str(uuid4())}).status_code == 409

    download_url = f"{ASSETS}/{asset_id}/download"
    assert client.get(download_url, headers=admin).status_code == 401
    download = client.get(download_url, headers=owner)
    assert download.content == content
    assert download.headers["X-Artifact-SHA256"] == checksum

    listing = {
        **scope, "artifact_id": asset_id, "product_id": asset["product_id"], "industry": "digital products",
        "title": "Workshop operations guide", "description": "An internal preview of the workshop operations guide and checklist.",
        "price_cents_cad": 2500, "request_key": "workshop-listing-01",
    }
    assert client.post(f"{FACTORY}/listing-drafts", headers=admin, json={**listing, "product_id": "other-product"}).status_code == 409

    def submit_and_approve(body):
        accepted = client.post(f"{FACTORY}/listing-drafts", headers=admin, json=body)
        assert accepted.status_code == 200, accepted.text
        action_id = accepted.json()["action_id"]
        approved = client.post(
            f"{FACTORY}/actions/{action_id}/approve", headers=owner, json={"confirmation": "APPROVE_INTERNAL_DRAFT"},
        )
        assert approved.status_code == 200, approved.text
        return action_id

    action_id = submit_and_approve(listing)
    executed = client.post(f"{FACTORY}/actions/run-once", headers=admin).json()
    assert executed["status"] == "completed"
    assert executed["receipt"]["sales_verified"] is False
    assert executed["receipt"]["product_asset"]["sha256"] == checksum
    with Session(engine) as db:
        artifact = db.get(MediaContent, executed["receipt"]["media_content_id"])
        assert json.loads(artifact.body)["product_asset"]["sha256"] == checksum
        assert json.loads(artifact.body)["purchase_url"] is None
    assert client.get(f"{FACTORY}/actions/{action_id}", headers=admin).json()["internal_artifact_verified"]

    pending_id = submit_and_approve({**listing, "request_key": "workshop-listing-02"})
    with Session(engine) as db:
        db.get(ProductArtifact, UUID(asset_id)).data = b"Bad storage bytes"
        db.commit()
    assert client.get(download_url, headers=owner).status_code == 409
    blocked = client.post(f"{FACTORY}/actions/run-once", headers=admin).json()
    assert blocked["action_id"] == pending_id
    assert blocked["reason"] == "Internal product artifact integrity mismatch"

    assert client.delete(f"{ASSETS}/{asset_id}", headers=admin).status_code == 401
    assert client.delete(f"{ASSETS}/{asset_id}", headers=owner).json()["revoked"]
    revoked_run = client.post(f"{FACTORY}/actions/run-once", headers=admin).json()
    assert revoked_run["action_id"] == pending_id
    assert revoked_run["reason"] == "Internal product artifact revoked"
    with Session(engine) as db:
        assert db.query(MediaContent).count() == 1
        learned = db.query(LegacyOrchestrationEvent).filter_by(event_type="MIMIR_INTERNAL_ARTIFACT_VERIFIED").one()
        assert json.loads(learned.payload_json)["product_asset"]["sha256"] == checksum
