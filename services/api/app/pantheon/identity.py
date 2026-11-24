"""Owner-enrolled signing identities for scoped specialist reports."""
from datetime import datetime, timezone
import hashlib
import os
import re
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from fastapi import HTTPException
from sqlalchemy import select

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent as Event
from app.services.prime_business_execution import _event, _json


KIND = "PANTHEON_WORKER_IDENTITY"
SIGNED_ROLES = frozenset({"ODIN", "NJORD"})


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def key_id(public_key):
    return hashlib.sha256(bytes.fromhex(public_key)).hexdigest()


def _load(db, identity_id, *, lock=False):
    if not isinstance(identity_id, str) or not re.fullmatch(r"[0-9a-f]{64}", identity_id):
        raise HTTPException(409, "Specialist identity is invalid")
    query = select(Event).filter_by(event_id=f"GID-{identity_id}", event_type=KIND)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(409, "Specialist identity is not enrolled")
    record = _json(row.payload_json, {})
    body = {k: v for k, v in record.items() if k != "sha256"} if isinstance(record, dict) else {}
    public_key = body.get("public_key", "")
    if (not isinstance(public_key, str) or not re.fullmatch(r"[0-9a-f]{64}", public_key)
            or key_id(public_key) != identity_id or body.get("identity_id") != identity_id
            or not isinstance(body.get("scope"), dict)
            or body.get("scope", {}).get("legacy_instance_id") != row.legacy_instance_id
            or artifact_digest(KIND, row.event_id, body) != record.get("sha256")):
        raise HTTPException(409, "Specialist identity evidence failed integrity verification")
    authority_body = {k: v for k, v in body.items() if k != "authority_signature"}
    trust_key = owner_trust_key()
    try:
        trust_key.verify(bytes.fromhex(body["authority_signature"]), authority_message(row.event_id, authority_body))
    except (InvalidSignature, KeyError, TypeError, ValueError):
        raise HTTPException(409, "Specialist enrollment lacks a valid owner-authority signature") from None
    return record


def worker_enrollment(db, signing_key):
    signer = key_id(signing_key.public_key().public_bytes_raw().hex())
    return signer, _load(db, signer)


def owner_trust_key():
    try:
        return Ed25519PublicKey.from_public_bytes(bytes.fromhex(
            os.getenv("VALHALLA_PANTHEON_ENROLLMENT_PUBLIC_KEY", ""),
        ))
    except ValueError:
        raise HTTPException(503, "Specialist enrollment verifier is unconfigured") from None


def authority_message(event_id, body):
    return bytes.fromhex(artifact_digest("pantheon_owner_enrollment", event_id, body))


def enroll(db, assignment, public_key, expires_at):
    identity_id = key_id(public_key)
    event_id = f"GID-{identity_id}"
    enrolled_at = now()
    if (assignment.state != "active" or not enrolled_at < expires_at <= assignment.expires_at):
        raise HTTPException(409, "Specialist identity lifetime exceeds the active assignment")
    body = {"identity_id": identity_id, "public_key": public_key, "assignment_id": str(assignment.id),
            "role": assignment.role, "scope": assignment.scope, "enrolled_at": enrolled_at.isoformat(),
            "expires_at": expires_at.isoformat()}
    try:
        authority = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(
            os.getenv("VALHALLA_PANTHEON_ENROLLMENT_PRIVATE_KEY", ""),
        ))
        if authority.public_key().public_bytes_raw() != owner_trust_key().public_bytes_raw():
            raise ValueError
        if authority.public_key().public_bytes_raw().hex() == public_key:
            raise HTTPException(409, "Owner enrollment key cannot be a specialist worker key")
    except ValueError:
        raise HTTPException(503, "Specialist enrollment signer is unconfigured") from None
    body["authority_signature"] = authority.sign(authority_message(event_id, body)).hex()
    body["sha256"] = artifact_digest(KIND, event_id, body)
    _event(db, event_id=event_id, legacy_instance_id=assignment.scope["legacy_instance_id"],
           event_type=KIND, message="Owner enrolled a scoped specialist identity", payload=body)
    return body


def revoke(db, identity_id):
    record = _load(db, identity_id, lock=True)
    event_id = f"GIR-{identity_id}"
    if not db.scalar(select(Event.id).filter_by(event_id=event_id)):
        _event(db, event_id=event_id, legacy_instance_id=record["scope"]["legacy_instance_id"],
               event_type=KIND, message="Owner revoked a scoped specialist identity",
               payload={"enrollment_sha256": record["sha256"]})
    return {"identity_id": identity_id, "state": "revoked"}


def authorize(db, identity_id, assignment_id, role, scope, *, current, observed=None):
    record = _load(db, identity_id, lock=current)
    if (record["assignment_id"], record["role"], record["scope"]) != (str(assignment_id), role, scope):
        raise HTTPException(409, "Specialist identity does not match assignment and scope")
    try:
        start, expires = (datetime.fromisoformat(record[k]) for k in ("enrolled_at", "expires_at"))
        if observed is not None and not start <= observed < expires:
            raise ValueError
        if current and not start <= now() < expires:
            raise ValueError
    except (TypeError, ValueError, KeyError):
        raise HTTPException(409, "Specialist identity was outside its authorized lifetime") from None
    if current and db.scalar(select(Event.id).filter_by(event_id=f"GIR-{identity_id}")):
        raise HTTPException(409, "Specialist identity is revoked")
    return record


def message(report):
    return bytes.fromhex(artifact_digest("pantheon_signed_worker_report", report["report_event_id"], report))


def verify_signature(db, report, *, current=False):
    try:
        body = {k: v for k, v in report.items() if k not in {"worker_signature", "report_sha256"}}
        assignment_id = UUID(body["assignment_id"])
        observed = datetime.fromisoformat(body["observed_at"])
        if observed.utcoffset() is None:
            raise ValueError
        observed = observed.astimezone(timezone.utc).replace(tzinfo=None)
        record = authorize(db, body["worker_identity_id"], assignment_id, body["role"], body["scope"],
                           current=current, observed=observed)
        signature = bytes.fromhex(report["worker_signature"])
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(record["public_key"])).verify(signature, message(body))
    except (InvalidSignature, KeyError, ValueError, TypeError):
        raise HTTPException(409, "Specialist worker signature failed integrity verification") from None
    return record
