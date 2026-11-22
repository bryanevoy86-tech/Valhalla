"""Verify signed metadata for a private professional opinion without authorizing reliance."""
from datetime import datetime, timezone
import json
import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import inspect

from app.loki.evidence import artifact_digest
from app.models.owner_conversation import OwnerAttachment, OwnerAttachmentReview
from app.schemas.tax_interpretations import TaxOpinionProvenanceIn
from app.services.owner_attachment_extraction import verified_attachment
from app.services.owner_attachment_review import latest_review, require_local_use


PROVENANCE_KEY = "signed_opinion_provenance_v1"


def signature_message(opinion, packet: TaxOpinionProvenanceIn) -> bytes:
    manifest = packet.model_dump(mode="json", exclude={"signature"})
    manifest.update(jurisdiction=opinion.jurisdiction, tax_year=opinion.tax_year, role=opinion.source,
                    specialist_id=str(opinion.specialist_id), case_id=str(opinion.case_id),
                    summary=opinion.summary, details=opinion.details, risk_level=opinion.risk_level)
    return artifact_digest("private_professional_opinion_v1", str(opinion.id), manifest).encode("ascii")


def verify_provenance(db, opinion, packet: TaxOpinionProvenanceIn, *, lock=False) -> None:
    today = datetime.now(timezone.utc).date()
    if (opinion.source not in {"lawyer", "accountant"} or opinion.specialist_id is None
            or not packet.issued_on <= today <= packet.valid_until):
        raise HTTPException(409, "Opinion role, identity or review dates are ineligible")

    # Only server-enrolled public keys can sign. No network verification or secret keys.
    try:
        enrollment = json.loads(os.getenv("VALHALLA_PROFESSIONAL_OPINION_PUBLIC_KEYS", "{}"))[packet.signer_key_id]
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(enrollment["public_key_hex"]))
        scopes = enrollment["jurisdictions"]
        if (enrollment["specialist_id"] != str(opinion.specialist_id) or enrollment["role"] != opinion.source
                or not isinstance(scopes, list) or opinion.jurisdiction not in scopes):
            raise ValueError("Signer scope mismatch")
        public_key.verify(bytes.fromhex(packet.signature), signature_message(opinion, packet))
    except (TypeError, KeyError, ValueError, InvalidSignature):
        raise HTTPException(409, "Opinion signature is invalid or its signer is outside the trusted scope") from None

    schema = inspect(db.connection())
    if any(not schema.has_table(model.__tablename__) for model in (OwnerAttachment, OwnerAttachmentReview)):
        raise HTTPException(503, "Private attachment and review storage is required")
    attachment = verified_attachment(db, packet.conversation_id, packet.attachment_id, lock=lock)
    require_local_use(db, attachment)
    review = latest_review(db, attachment)
    if (attachment.sha256 != packet.source_sha256 or review is None
            or review.disposition != "ACCEPT_LOCAL"):
        raise HTTPException(409, "The exact opinion file requires private owner review")


def current_provenance(db, opinion):
    stored = (opinion.flags or {}).get(PROVENANCE_KEY)
    if stored is None:
        return None
    try:
        packet = TaxOpinionProvenanceIn.model_validate(stored)
        verify_provenance(db, opinion, packet)
    except (HTTPException, ValidationError):
        return {"status": "UNAVAILABLE_OR_INVALID"}
    return {"status": "SCOPED_SIGNATURE_VERIFIED", "attachment_id": str(packet.attachment_id),
            "source_sha256": packet.source_sha256, "issued_on": packet.issued_on.isoformat(),
            "valid_until": packet.valid_until.isoformat()}
