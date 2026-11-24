"""Verify separately issued acceptance evidence without enabling effect adapters."""
from datetime import datetime, timezone
import os
from typing import Annotated, Literal
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi import HTTPException
from pydantic import AwareDatetime, Field
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.go_live_state import GoLiveState
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.go_live import DEFAULT_ROW_ID
from app.services.launch_readiness import CHANNEL_REQUIREMENTS, COMMON_REQUIREMENTS
from app.services.prime_business_execution import _check_legacy, _emergency_stop_active, _event, _json


KIND = "CHANNEL_COMMISSIONING_ACCEPTANCE"
Sha = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class Acceptance(StrictModel):
    evidence_id: UUID
    scope: MarketScope
    channel: str
    authority_sha256: Sha
    basis: Literal["DISPOSABLE_FIXTURE", "STAGING_PROVIDER_READBACK"]
    observed_at: AwareDatetime
    expires_at: AwareDatetime
    requirements: dict[str, Sha] = Field(max_length=20)
    signature: str = Field(pattern=r"^[0-9a-f]{128}$")


class Request(StrictModel):
    scope: MarketScope
    channel: str
    evidence_id: UUID
    authority_sha256: Sha


def signature_message(value):
    body = value.model_dump(mode="json", exclude={"signature"})
    return bytes.fromhex(artifact_digest(KIND, str(value.evidence_id), body))


def requirements(channel):
    if channel not in CHANNEL_REQUIREMENTS:
        raise HTTPException(422, "Unknown release channel")
    return {*COMMON_REQUIREMENTS, *CHANNEL_REQUIREMENTS[channel]}


def verify(value, now):
    required = requirements(value.channel)
    if value.basis == "STAGING_PROVIDER_READBACK" and os.getenv("APP_ENV") != "staging":
        raise HTTPException(409, "Provider readback evidence requires the isolated staging API")
    if not (value.observed_at <= now < value.expires_at
            and (value.expires_at - value.observed_at).total_seconds() <= 86400):
        raise HTTPException(409, "Commissioning evidence is stale or outside the observation window")
    if set(value.requirements) != required or len(set(value.requirements.values())) != len(required):
        raise HTTPException(409, "Commissioning evidence does not cover the exact independent requirements")
    try:
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(
            os.getenv("VALHALLA_COMMISSIONING_OBSERVER_PUBLIC_KEY", ""),
        ))
    except ValueError:
        raise HTTPException(503, "Commissioning observer is not configured") from None
    try:
        key.verify(bytes.fromhex(value.signature), signature_message(value))
    except InvalidSignature:
        raise HTTPException(409, "Commissioning observer signature is invalid") from None


def record(db, value):
    ensure_journal(db)
    verify(value, datetime.now(timezone.utc))
    scope = value.scope.model_dump()
    _check_legacy(db, **scope, lock=True)
    key = f"CCE-{value.evidence_id}"
    data = value.model_dump(mode="json")
    digest = artifact_digest(KIND, key, data)
    row = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=key))
    if row is None:
        _event(db, event_id=key, legacy_instance_id=scope["legacy_instance_id"], event_type=KIND,
               message="Signed staging acceptance evidence received", payload={"value": data, "sha256": digest})
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            row = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=key))
            if row is None:
                raise
    if row is not None and (row.event_type != KIND or row.legacy_instance_id != scope["legacy_instance_id"] or _json(
        row.payload_json, {},
    ) != {"value": data, "sha256": digest}):
        raise HTTPException(409, "Commissioning evidence ID already binds a different observation")
    return {"evidence_id": value.evidence_id, "sha256": digest, "external_authority": False}


def ensure_journal(db):
    labels = {os.getenv("APP_ENV", "").strip().lower(), os.getenv("ENV", "").strip().lower()} - {""}
    if not labels or not labels <= {"dev", "test", "sandbox", "staging"}:
        raise HTTPException(503, "Commissioning preview is available only in isolated environments")
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Commissioning evidence journal is unavailable")


def evaluate(db, request):
    ensure_journal(db)
    requirements(request.channel)
    scope = request.scope.model_dump()
    _check_legacy(db, **scope)
    key = f"CCE-{request.evidence_id}"
    row = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=key, event_type=KIND))
    if row is None or row.legacy_instance_id != scope["legacy_instance_id"]:
        raise HTTPException(409, "No exact commissioning evidence exists")
    payload = _json(row.payload_json, {})
    try:
        data = payload["value"]
        if payload["sha256"] != artifact_digest(KIND, key, data):
            raise ValueError
        evidence = Acceptance.model_validate(data)
    except (KeyError, TypeError, ValueError):
        raise HTTPException(409, "Commissioning evidence failed integrity") from None
    if (evidence.evidence_id, evidence.scope, evidence.channel, evidence.authority_sha256) != (
        request.evidence_id, request.scope, request.channel, request.authority_sha256,
    ):
        raise HTTPException(409, "Commissioning evidence does not match the requested scope or authority digest")
    verify(evidence, datetime.now(timezone.utc))
    state = (db.get(GoLiveState, DEFAULT_ROW_ID)
             if inspect(db.connection()).has_table(GoLiveState.__tablename__) else None)
    stopped = state is None or _emergency_stop_active(db)
    return {"status": "HELD" if stopped else "READY_FOR_OWNER_SCOPE_REVIEW",
            "scope": scope, "channel": request.channel, "basis": evidence.basis,
            "evidence_sha256": payload["sha256"], "emergency_stop_clear": not stopped,
            "standing_mandate_verified": False, "commercial_release": False,
            "external_authority": False}
