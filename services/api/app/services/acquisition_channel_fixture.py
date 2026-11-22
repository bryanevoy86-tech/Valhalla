"""Replay an exact campaign media intent without a transport, spend or publication."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import AwareDatetime, Field
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.foundry_checkout import FoundryCampaignVisit
from app.models.media_engine import MediaChannel, MediaContent, MediaPublishLog
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.acquisition_rehearsal import (
    AcquisitionPlanIn, consent_event_id, customer_reference, journal_event, make_plan, read_plan, verify_consent,
)
from app.services.prime_business_execution import _check_legacy, _emergency_stop_active, _event, _json
from app.services.economic_control import require_no_containment
from app.services.specialist_triggers import outcome_scope_key

INTENT = "ACQUISITION_CHANNEL_FIXTURE_INTENT"
RESULT = "ACQUISITION_CHANNEL_FIXTURE_RECEIPT"
CLAIM = "ACQUISITION_CHANNEL_FIXTURE_EVENT_CLAIM"


class ChannelIntentIn(StrictModel):
    intent_id: UUID
    scope: MarketScope
    campaign_id: int = Field(strict=True, gt=0)
    media_publish_id: int = Field(strict=True, gt=0)
    scheduled_at: AwareDatetime
    reviewed_transparent_copy: Literal[True]
    visit_id: UUID | None = None


class ChannelReceiptIn(StrictModel):
    intent_id: UUID
    scope: MarketScope
    provider_fixture_event_id: UUID
    expected_intent_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    outcome: Literal["ACCEPTED_IN_FIXTURE", "REJECTED_IN_FIXTURE"]


def _ready(db):
    required = (LegacyOrchestrationEvent, FoundryCampaignVisit, MediaChannel, MediaContent, MediaPublishLog)
    inspector = inspect(db.connection())
    if not all(inspector.has_table(model.__tablename__) for model in required):
        raise HTTPException(503, "Acquisition channel rehearsal schema unavailable")


def _receipt(db, ref, kind, scope):
    row = journal_event(db, ref)
    if row is None:
        return None
    payload = _json(row.payload_json, {})
    if (not isinstance(payload, dict) or payload.get("scope") != scope or row.event_type != kind
            or row.legacy_instance_id != scope["legacy_instance_id"]):
        raise HTTPException(409, "Channel fixture journal scope or identity mismatch")
    content = {k: v for k, v in payload.items() if k != "sha256"}
    if payload.get("sha256") != artifact_digest(kind, ref, content):
        raise HTTPException(409, "Channel fixture journal integrity mismatch")
    return payload


def _write(db, ref, kind, value):
    _event(db, event_id=ref, event_type=kind, legacy_instance_id=value["scope"]["legacy_instance_id"],
           message="Acquisition channel rehearsal evidence", payload=value)


def _commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Channel fixture identity was already recorded; retry the original request") from None


def _binding(db, request, now):
    scope = request.scope.model_dump()
    plan = read_plan(db, request.campaign_id, scope)
    if plan is None:
        raise HTTPException(404, "Campaign plan not found")
    recorded = AcquisitionPlanIn.model_validate(plan["request"])
    current = make_plan(db, request.campaign_id, recorded, now.date())
    if any(current.get(key) != plan.get(key) for key in ("demand_sha256", "consumer_research")):
        raise HTTPException(409, "Campaign evidence has changed")
    publish = db.get(MediaPublishLog, request.media_publish_id, with_for_update=True)
    if publish is None or publish.status != "planned" or publish.external_ref or publish.published_at:
        raise HTTPException(409, "An unpublished planned media entry is required")
    content, channel = db.get(MediaContent, publish.content_id), db.get(MediaChannel, publish.channel_id)
    if content is None or content.audience != "internal" or channel is None or not channel.is_active:
        raise HTTPException(409, "Reviewed internal media and an active channel are required")
    direct = recorded.channel == "DIRECT_OPT_IN"
    if direct != (request.visit_id is not None):
        raise HTTPException(409, "Direct channel rehearsal requires a scoped opt-in visit")
    consent = None
    if request.visit_id is not None:
        visit = db.get(FoundryCampaignVisit, request.visit_id)
        if visit is None or visit.campaign_id != request.campaign_id or visit.scope_key != outcome_scope_key(scope):
            raise HTTPException(409, "Visit is not attributed to the scoped campaign")
        consent = verify_consent(journal_event(db, consent_event_id(visit.id)), scope, request.campaign_id, visit.id)
        ref, _ = customer_reference(scope, UUID(consent["consent_fixture_id"]))
        if journal_event(db, ref) is not None:
            raise HTTPException(409, "Synthetic customer is suppressed")
    media = {"publish_id": publish.id, "media_channel_id": channel.id, "slug": channel.slug,
             "content_id": content.id, "title": content.title, "body": content.body, "audience": content.audience}
    return {"plan_sha256": plan["sha256"], "media_sha256": artifact_digest("planned_media", str(publish.id), media),
            "channel": recorded.channel, "consent_sha256": consent["sha256"] if consent else None}


def _guard(db, scope):
    _ready(db)
    _check_legacy(db, **scope, lock=True)
    if _emergency_stop_active(db):
        raise HTTPException(503, "Acquisition channel rehearsal paused by emergency stop")
    require_no_containment(db, scope)


def stage_channel(db, request: ChannelIntentIn, now=None):
    now = now or datetime.now(timezone.utc)
    scope = request.scope.model_dump()
    _guard(db, scope)
    ref = f"ACQ-CHANNEL-{request.intent_id}"
    previous = _receipt(db, ref, INTENT, scope)
    inputs = request.model_dump(mode="json")
    if previous is not None:
        if previous["request"] != inputs:
            raise HTTPException(409, "Channel intent ID already used")
        return previous
    if not now - timedelta(minutes=5) <= request.scheduled_at <= now + timedelta(days=7):
        raise HTTPException(422, "Channel intent schedule outside the rehearsal window")
    value = {"scope": scope, "request": inputs, "binding": _binding(db, request, now),
             "status": "PLANNED_FIXTURE", "external_action_authorized": False, "publication_verified": False}
    value["sha256"] = artifact_digest(INTENT, ref, value)
    _write(db, ref, INTENT, value)
    _commit(db)
    return value


def _verify_signature(request, signature):
    key = os.getenv("VALHALLA_ACQUISITION_CHANNEL_FIXTURE_KEY")
    if not key or key in {os.getenv(name) for name in (
        "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "VALHALLA_FOUNDRY_FIXTURE_SECRET",
        "VALHALLA_PRIME_CONTROL_KEY", "VALHALLA_OWNER_MANDATE_KEY",
    )}:
        raise HTTPException(503, "Dedicated acquisition fixture signing key unavailable")
    data = request.model_dump(mode="json")
    digest = artifact_digest("acquisition_channel_provider_fixture", str(request.provider_fixture_event_id), data)
    expected = hmac.new(key.encode(), digest.encode(), hashlib.sha256).hexdigest()
    if not signature or not signature.isascii() or not hmac.compare_digest(signature, expected):
        raise HTTPException(401, "Invalid acquisition channel fixture signature")
    return data


def accept_channel_receipt(db, request: ChannelReceiptIn, signature, now=None):
    data = _verify_signature(request, signature)
    now = now or datetime.now(timezone.utc)
    scope = request.scope.model_dump()
    _guard(db, scope)
    ref = f"ACQ-CHANNEL-RESULT-{request.intent_id}"
    previous = _receipt(db, ref, RESULT, scope)
    if previous is not None:
        if previous["receipt"] != data:
            raise HTTPException(409, "Channel receipt differs from the recorded outcome")
        return previous
    intent = _receipt(db, f"ACQ-CHANNEL-{request.intent_id}", INTENT, scope)
    if intent is None or request.expected_intent_sha256 != intent["sha256"]:
        raise HTTPException(409, "Channel receipt does not bind the recorded intent")
    intended = ChannelIntentIn.model_validate(intent["request"])
    if not intended.scheduled_at <= now <= intended.scheduled_at + timedelta(hours=24):
        raise HTTPException(409, "Channel receipt outside the scheduled rehearsal window")
    if _binding(db, intended, now) != intent["binding"]:
        raise HTTPException(409, "Reviewed campaign, media or opt-in evidence has changed")
    claim_ref = f"ACQ-CHANNEL-EVENT-{request.provider_fixture_event_id}"
    if journal_event(db, claim_ref) is not None:
        raise HTTPException(409, "Acquisition fixture provider event already used")
    claim = {"scope": scope, "intent_id": str(request.intent_id)}
    claim["sha256"] = artifact_digest(CLAIM, claim_ref, claim)
    _write(db, claim_ref, CLAIM, claim)
    value = {"scope": scope, "receipt": data, "status": request.outcome,
             "external_action_authorized": False, "publication_verified": False}
    value["sha256"] = artifact_digest(RESULT, ref, value)
    _write(db, ref, RESULT, value)
    _commit(db)
    return value
