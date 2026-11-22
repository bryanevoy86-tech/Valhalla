from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from uuid import UUID, uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from sqlalchemy.orm import Session

from app.models.owner_conversation import OwnerAttachment, OwnerAttachmentReview, OwnerConversation
from app.models.tax_interpretations import TaxOpinion
from app.schemas.tax_interpretations import TaxOpinionProvenanceIn, TaxOpinionRelianceIn
from app.services.tax_opinion_provenance import PROVENANCE_KEY, reliance_signature_message, signature_message


def test_opinion_signature_requires_exact_private_file_and_trusted_specialist(deal_client, monkeypatch):
    client, engine = deal_client
    owner = {"X-Owner-Mandate-Key": "fixture-opinion-owner"}
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    for model in (TaxOpinion, OwnerConversation, OwnerAttachment, OwnerAttachmentReview):
        model.__table__.create(engine)
    specialist_id, conversation_id, attachment_id = (uuid4() for _ in range(3))
    file_bytes = b"Independent fixture opinion. No legal or tax advice."
    digest = sha256(file_bytes).hexdigest()
    with Session(engine) as db:
        db.add(OwnerConversation(id=conversation_id, title="Private fixture review"))
        db.add(OwnerAttachment(id=attachment_id, conversation_id=conversation_id, filename="opinion.txt",
                               media_type="text/plain", sha256=digest, data=file_bytes, size_bytes=len(file_bytes)))
        db.commit()

    path = "/tax-bridge/opinions"
    intake = client.post(path, headers=owner, json={
        "jurisdiction": "CA-CRA", "source": "accountant", "tax_year": "2026", "specialist_id": str(specialist_id),
        "summary": "Fixture opinion",
        "flags": {PROVENANCE_KEY: "untrusted", "reliance_authorized": True, "professional_signoff_verified": True},
    })
    assert intake.status_code == 200, intake.text
    assert intake.headers["cache-control"] == "no-store"
    assert intake.json()["flags"] == {"reliance_authorized": False, "professional_signoff_verified": False}
    opinion_id = intake.json()["id"]
    private_key = Ed25519PrivateKey.generate()
    enrollment = {"fixture-key": {
        "public_key_hex": private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex(),
        "specialist_id": str(specialist_id), "role": "accountant", "jurisdictions": ["CA-CRA"],
    }}
    today = datetime.now(timezone.utc).date()
    review = {"conversation_id": str(conversation_id), "attachment_id": str(attachment_id),
              "source_sha256": digest, "signer_key_id": "fixture-key", "issued_on": today.isoformat(),
              "valid_until": (today + timedelta(days=10)).isoformat(), "signature": "0" * 128}
    with Session(engine) as db:
        packet = TaxOpinionProvenanceIn.model_validate(review)
        review["signature"] = private_key.sign(signature_message(db.get(TaxOpinion, UUID(opinion_id)), packet)).hex()

    endpoint = f"{path}/{opinion_id}/provenance"
    assert client.post(endpoint, json=review).status_code == 401
    monkeypatch.setenv("VALHALLA_PROFESSIONAL_OPINION_PUBLIC_KEYS", "{}")
    assert client.post(endpoint, headers=owner, json=review).status_code == 409
    monkeypatch.setenv("VALHALLA_PROFESSIONAL_OPINION_PUBLIC_KEYS", json.dumps(enrollment))
    assert client.post(endpoint, headers=owner, json={**review, "source_sha256": "0" * 64}).status_code == 409
    assert client.post(endpoint, headers=owner, json=review).status_code == 409
    with Session(engine) as db:
        db.add(OwnerAttachmentReview(id=uuid4(), attachment_id=attachment_id, source_sha256=digest,
                                     disposition="ACCEPT_LOCAL", reason="Fixture is authorized for local review"))
        db.commit()

    verified = client.post(endpoint, headers=owner, json=review)
    assert verified.status_code == 200, verified.text
    flags = verified.json()["flags"]
    assert flags["professional_opinion_provenance"]["status"] == "SCOPED_SIGNATURE_VERIFIED"
    assert flags["professional_opinion_provenance"]["source_sha256"] == digest
    assert PROVENANCE_KEY not in flags and flags["reliance_authorized"] is False
    assert client.post(endpoint, headers=owner, json=review).json() == verified.json()

    assert_scoped_reliance(client, engine, monkeypatch, owner, opinion_id, today, enrollment, private_key,
                           flags["professional_opinion_provenance"]["provenance_sha256"])

    monkeypatch.setenv("VALHALLA_PROFESSIONAL_OPINION_PUBLIC_KEYS", "{}")
    read = f"{path}/{opinion_id}"
    assert client.get(read).json()["flags"]["professional_opinion_provenance"]["status"] == "UNAVAILABLE_OR_INVALID"
    monkeypatch.setenv("VALHALLA_PROFESSIONAL_OPINION_PUBLIC_KEYS", json.dumps(enrollment))
    with Session(engine) as db:
        attachment = db.get(OwnerAttachment, attachment_id)
        attachment.deleted_at = datetime.now(timezone.utc)
        attachment.deletion_reason = "OWNER_REQUEST"
        attachment.data = None
        db.commit()
    assert client.get(read).json()["flags"]["professional_opinion_provenance"]["status"] == "UNAVAILABLE_OR_INVALID"



def assert_scoped_reliance(client, engine, monkeypatch, owner, opinion_id, today, signer_enrollments, author_key, digest):
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    review_key = Ed25519PrivateKey.generate()
    reviewers = {**signer_enrollments, "qualified-fixture": {
        "public_key_hex": review_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex(),
        "specialist_id": str(uuid4()), "role": "accountant", "jurisdictions": ["CA-CRA"], "qualified_reviewer": True,
    }}
    monkeypatch.setenv("VALHALLA_PROFESSIONAL_OPINION_PUBLIC_KEYS", json.dumps(reviewers))
    scope = {"decision_reference": "structure-fixture-1", "purpose": "INTERNAL_STRUCTURE_REVIEW"}
    grant = {**scope, "approval_id": str(uuid4()), "expected_provenance_sha256": digest,
             "reviewer_key_id": "qualified-fixture", "reviewed_on": today.isoformat(),
             "valid_until": (today + timedelta(days=2)).isoformat(), "signature": "0" * 128}

    def sign(data, key):
        with Session(engine) as db:
            message = reliance_signature_message(db.get(TaxOpinion, UUID(opinion_id)),
                                                 TaxOpinionRelianceIn.model_validate(data))
        return {**data, "signature": key.sign(message).hex()}

    endpoint = f"/tax-bridge/opinions/{opinion_id}/reliance"
    status = f"{endpoint}/{grant['approval_id']}/check"
    revoke = f"{endpoint}/{grant['approval_id']}/revoke"
    assert client.post(endpoint, headers=owner, json=sign(grant, author_key)).status_code == 409
    signed = sign(grant, review_key)
    assert client.post(endpoint, json=signed).status_code == 401
    tampered = {**signed, "decision_reference": "another-private-decision"}
    assert client.post(endpoint, headers=owner, json=tampered).status_code == 409
    approved = client.post(endpoint, headers=owner, json=signed)
    assert approved.status_code == 200, approved.text
    assert approved.json()["execution_authorized"] is False
    assert client.post(endpoint, headers=owner, json=signed).json() == approved.json()
    assert client.post(status, json=scope).json()["reliance_authorized"] is True
    assert client.post(status, json={**scope, "purpose": "INTERNAL_RISK_ASSESSMENT"}).status_code == 409

    monkeypatch.setenv("VALHALLA_PROFESSIONAL_OPINION_PUBLIC_KEYS", json.dumps(signer_enrollments))
    assert client.post(status, json=scope).status_code == 409
    monkeypatch.setenv("VALHALLA_PROFESSIONAL_OPINION_PUBLIC_KEYS", json.dumps(reviewers))
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    assert client.post(status, json=scope).status_code == 503
    withdrawn = client.post(revoke, headers=owner, json={"reason": "Withdraw fixture approval"})
    assert withdrawn.status_code == 200, withdrawn.text
    assert client.post(revoke, headers=owner, json={"reason": "Withdraw fixture approval"}).json() == withdrawn.json()
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    assert client.post(status, json=scope).status_code == 409
    assert client.post(endpoint, headers=owner, json=signed).status_code == 409
