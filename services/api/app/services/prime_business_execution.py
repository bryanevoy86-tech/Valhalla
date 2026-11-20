"""Heimdall Prime: first durable, owner-gated Business Factory execution lane.

This pilot has ONE verified, local action: write a digital-product listing
DRAFT into the existing media_contents table. It never posts externally,
charges money, sends messages, or asserts commercial success.

The canonical legacy work registry supplies durable assignments and events.
Transaction boundaries plus PostgreSQL row locks protect processing.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.models.completion_registry import (
    LegacyInstanceRegistryItem,
    LegacyInstanceWorkItem,
    LegacyOrchestrationEvent,
)
from app.models.media_engine import MediaContent
from app.core.autonomy_governor import require_internal_draft
from sqlalchemy import inspect


ACTION_TYPE = "draft_product_listing_v1"
APPROVAL_EVENT = "FACTORY_OWNER_APPROVED"
RECEIPT_EVENT = "FACTORY_ARTIFACT_VERIFIED"
MAX_BODY_LENGTH = 5000


def require_factory_key(
    provided: str | None = Header(default=None, alias="X-Business-Factory-Key"),
) -> None:
    """Admin-only; missing configuration must deny all API access."""
    expected = os.environ.get("VALHALLA_FACTORY_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Business Factory admin key not configured")
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Business Factory authentication required")


def require_owner_mandate_key(
    provided: str | None = Header(default=None, alias="X-Owner-Mandate-Key"),
) -> None:
    """Separate grant authority from unattended execution credentials."""
    expected = os.environ.get("VALHALLA_OWNER_MANDATE_KEY", "")
    worker_key = os.environ.get("VALHALLA_FACTORY_KEY", "")
    prime_key = os.environ.get("VALHALLA_PRIME_CONTROL_KEY", "")
    if not expected or expected in {worker_key, prime_key}:
        raise HTTPException(status_code=503, detail="Distinct owner mandate key not configured")
    if not provided or not hmac.compare_digest(provided.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Owner mandate authentication required")


def _json(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value) if value else fallback
    except (TypeError, json.JSONDecodeError):
        return fallback


def _canonical(data: dict) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _approval_id(action_id: str) -> str:
    return f"BF-APPROVED-{action_id}"


def _receipt_id(action_id: str) -> str:
    return f"BF-RECEIPT-{action_id}"


def _check_legacy(
    db: Session,
    *,
    legacy_instance_id: str,
    business_id: str,
    engine_id: str,
    jurisdiction: str,
) -> LegacyInstanceRegistryItem:
    row = db.query(LegacyInstanceRegistryItem).filter(
        LegacyInstanceRegistryItem.legacy_instance_id == legacy_instance_id
    ).first()
    if row is None:
        raise HTTPException(status_code=409, detail="legacy instance is not registered")
    if row.status not in {"PASS", "PARTIAL"}:
        raise HTTPException(status_code=409, detail="legacy instance not eligible for internal drafts")
    if row.isolation_state != "ISOLATED" or row.synchronization_status != "SYNCED":
        raise HTTPException(status_code=409, detail="legacy instance isolation/policy sync not verified")
    if row.failover_state != "NOT_TRIGGERED":
        raise HTTPException(status_code=409, detail="legacy instance failover state blocks execution")
    context = _json(row.local_knowledge_context_json, {})
    if not isinstance(context, dict):
        raise HTTPException(status_code=409, detail="invalid legacy context")
    if (
        context.get("jurisdiction") != jurisdiction
        or context.get("business_id") != business_id
        or business_id not in _json(row.assigned_businesses_json, [])
        or jurisdiction not in _json(row.assigned_jurisdictions_json, [])
        or engine_id not in _json(row.engines_json, [])
    ):
        raise HTTPException(status_code=409, detail="legacy business, engine, or jurisdiction mismatch")
    return row


def _event(
    db: Session,
    *,
    event_id: str,
    legacy_instance_id: str,
    event_type: str,
    message: str,
    payload: dict[str, Any],
) -> None:
    db.add(
        LegacyOrchestrationEvent(
            event_id=event_id,
            legacy_instance_id=legacy_instance_id,
            event_type=event_type,
            severity="info",
            message=message,
            payload_json=_canonical(payload),
        )
    )


def _emergency_stop_active(db: Session) -> bool:
    """Read runtime emergency stop from trusted config and existing DB state.

    This internal-only draft pilot tolerates an absent historical GoLiveState
    table for isolated test databases. External actions never use this
    exception. A present but unreadable state fails closed.
    """
    if os.environ.get("VALHALLA_EMERGENCY_STOP", "").strip().lower() in {
        "1", "true", "yes", "on",
    }:
        return True
    try:
        if not inspect(db.get_bind()).has_table("go_live_state"):
            return False
        from app.models.go_live_state import GoLiveState

        state = db.query(GoLiveState).filter(GoLiveState.id == 1).first()
        return bool(state and state.kill_switch_engaged)
    except Exception:
        return True


def _internal_policy_decision(
    db: Session, item: LegacyInstanceWorkItem, approved: bool,
):
    return require_internal_draft(
        action_id=item.action_id,
        business_id=item.business_id,
        legacy_id=item.legacy_instance_id,
        approved=approved,
        emergency_stop=_emergency_stop_active(db),
    )


MANDATE_GRANT = "FACTORY_MANDATE_GRANTED"
MANDATE_REVOKE = "FACTORY_MANDATE_REVOKED"


def _mandate_digest(mandate_id: str) -> str:
    return hashlib.sha256(mandate_id.encode("utf-8")).hexdigest()


def _mandate_event_id(mandate_id: str) -> str:
    return "BF-MANDATE-" + _mandate_digest(mandate_id)


def _mandate_revocation_id(mandate_id: str) -> str:
    return "BF-REVOKE-" + _mandate_digest(mandate_id)


def _mandate_use_type(mandate_id: str) -> str:
    return "BF-MANDATE-USE-" + _mandate_digest(mandate_id)


def _lock_mandate(db: Session, mandate_id: str):
    return db.query(LegacyOrchestrationEvent).filter(
        LegacyOrchestrationEvent.event_id == _mandate_event_id(mandate_id),
        LegacyOrchestrationEvent.event_type == MANDATE_GRANT,
    ).with_for_update().first()


def grant_draft_mandate(db: Session, request: Any) -> dict:
    """Grant finite standing authority for ONE product's local drafts only."""
    if _emergency_stop_active(db):
        raise HTTPException(status_code=409, detail="EMERGENCY_STOP_ACTIVE")
    _check_legacy(db, legacy_instance_id=request.legacy_instance_id,
                  business_id=request.business_id, engine_id=request.engine_id,
                  jurisdiction=request.jurisdiction)
    if _lock_mandate(db, request.mandate_id):
        raise HTTPException(status_code=409, detail="Mandate ID already used")
    grant = {
        "mandate_id": request.mandate_id,
        "legacy_instance_id": request.legacy_instance_id,
        "business_id": request.business_id,
        "engine_id": request.engine_id,
        "jurisdiction": request.jurisdiction,
        "product_id": request.product_id,
        "scope": "INTERNAL_DRAFT_ONLY",
        "expires_at_epoch": int(time.time()) + request.ttl_seconds,
        "max_uses": request.max_uses,
        "max_price_cents_cad": request.max_price_cents_cad,
        "external_effects_authorized": False,
    }
    _event(db, event_id=_mandate_event_id(request.mandate_id),
           legacy_instance_id=request.legacy_instance_id, event_type=MANDATE_GRANT,
           message="Owner granted finite internal-draft standing authority", payload=grant)
    db.commit()
    return grant


def revoke_draft_mandate(db: Session, mandate_id: str) -> dict:
    # Lock the same row as the worker so revocation and consumption serialize.
    row = _lock_mandate(db, mandate_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Mandate not found")
    if not db.query(LegacyOrchestrationEvent).filter_by(
        event_id=_mandate_revocation_id(mandate_id)
    ).first():
        _event(db, event_id=_mandate_revocation_id(mandate_id),
               legacy_instance_id=row.legacy_instance_id, event_type=MANDATE_REVOKE,
               message="Owner revoked standing draft authority", payload={"mandate_id": mandate_id})
    db.commit()
    return {"mandate_id": mandate_id, "status": "revoked", "external_effects_authorized": False}


def _check_draft_mandate(db: Session, item: LegacyInstanceWorkItem, payload: dict) -> str | None:
    """Called within the actual draft transaction. Holds grant lock to commit."""
    mandate_id = payload.get("mandate_id")
    if not isinstance(mandate_id, str) or not 8 <= len(mandate_id) <= 64:
        return "MANDATE_MISSING_OR_INVALID"
    row = _lock_mandate(db, mandate_id)
    if row is None:
        return "MANDATE_NOT_FOUND"
    if db.query(LegacyOrchestrationEvent).filter_by(event_id=_mandate_revocation_id(mandate_id)).first():
        return "MANDATE_REVOKED"
    grant = _json(row.payload_json, {})
    if not isinstance(grant, dict):
        return "MANDATE_INVALID"
    if (
        grant.get("mandate_id") != mandate_id
        or grant.get("scope") != "INTERNAL_DRAFT_ONLY"
        or grant.get("external_effects_authorized") is not False
        or row.legacy_instance_id != item.legacy_instance_id
        or grant.get("legacy_instance_id") != item.legacy_instance_id
        or grant.get("business_id") != item.business_id
        or grant.get("engine_id") != item.engine_id
        or grant.get("jurisdiction") != item.jurisdiction
        or grant.get("product_id") != payload.get("product_id")
    ):
        return "MANDATE_SCOPE_MISMATCH"
    expires, maximum, max_price = (grant.get(k) for k in (
        "expires_at_epoch", "max_uses", "max_price_cents_cad"))
    price = payload.get("price_cents_cad")
    if any(type(v) is not int for v in (expires, maximum, max_price, price)):
        return "MANDATE_INVALID"
    if expires <= int(time.time()):
        return "MANDATE_EXPIRED"
    if not 1 <= maximum <= 100 or not 1 <= price <= max_price <= 10_000_000:
        return "MANDATE_LIMIT_EXCEEDED"
    used = db.query(LegacyOrchestrationEvent).filter_by(
        event_type=_mandate_use_type(mandate_id), legacy_instance_id=item.legacy_instance_id
    ).count()
    if used >= maximum:
        return "MANDATE_EXHAUSTED"
    return None


def submit_listing_draft(db: Session, request: Any) -> dict:
    """Persist an idempotent work assignment; NO action occurs at submission."""
    inputs = {
        "action_type": ACTION_TYPE,
        "business_id": request.business_id,
        "product_id": request.product_id,
        "title": request.title,
        "description": request.description,
        "price_cents_cad": request.price_cents_cad,
        "currency": "CAD",
        "mode": "INTERNAL_DRAFT_ONLY",
    }
    if getattr(request, "mandate_id", None):
        inputs["mandate_id"] = request.mandate_id
    key_hash = hashlib.sha256(
        f"{request.legacy_instance_id}:{request.request_key}".encode("utf-8")
    ).hexdigest()
    action_id = "bfd_" + key_hash[:32]
    idem_key = "bfv1_" + key_hash

    existing = db.query(LegacyInstanceWorkItem).filter(
        LegacyInstanceWorkItem.idempotency_key == idem_key
    ).first()
    if existing:
        if (
            existing.legacy_instance_id != request.legacy_instance_id
            or existing.business_id != request.business_id
            or existing.engine_id != request.engine_id
            or existing.industry != request.industry
            or existing.jurisdiction != request.jurisdiction
            or existing.payload_json != _canonical(inputs)
        ):
            raise HTTPException(status_code=409, detail="idempotency key reused with different work")
        return {"action_id": existing.action_id, "status": existing.status, "duplicate": True}

    instance = _check_legacy(
        db,
        legacy_instance_id=request.legacy_instance_id,
        business_id=request.business_id,
        engine_id=request.engine_id,
        jurisdiction=request.jurisdiction,
    )
    local = _json(instance.local_knowledge_context_json, {})
    item = LegacyInstanceWorkItem(
        action_id=action_id,
        idempotency_key=idem_key,
        legacy_instance_id=request.legacy_instance_id,
        business_id=request.business_id,
        industry=request.industry,
        jurisdiction=request.jurisdiction,
        engine_id=request.engine_id,
        objective=f"Create a verified INTERNAL listing draft for {request.product_id}",
        status="queued",
        risk_profile="no_external_effects",
        integration_profile="none",
        namespace=local.get("data_namespace") or f"factory/{request.legacy_instance_id}",
        payload_json=_canonical(inputs),
    )
    db.add(item)
    _event(
        db,
        event_id=f"BF-QUEUED-{action_id}",
        legacy_instance_id=item.legacy_instance_id,
        event_type="FACTORY_WORK_QUEUED",
        message="Internal product listing draft queued, awaiting owner approval",
        payload={"action_id": action_id, "action_type": ACTION_TYPE},
    )
    db.commit()
    return {"action_id": action_id, "status": "queued", "duplicate": False}


def approve_action(db: Session, action_id: str, confirmation: str) -> dict:
    if confirmation != "APPROVE_INTERNAL_DRAFT":
        raise HTTPException(status_code=422, detail="explicit internal-draft confirmation required")

    if _emergency_stop_active(db):
        raise HTTPException(status_code=409, detail="EMERGENCY_STOP_ACTIVE")

    item = db.query(LegacyInstanceWorkItem).filter(
        LegacyInstanceWorkItem.action_id == action_id
    ).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="action not found")
    if item.status != "queued":
        raise HTTPException(status_code=409, detail="only queued work may be approved")
    payload = _json(item.payload_json, {})
    if payload.get("action_type") != ACTION_TYPE or payload.get("mode") != "INTERNAL_DRAFT_ONLY":
        raise HTTPException(status_code=409, detail="unsupported execution action")
    _check_legacy(
        db,
        legacy_instance_id=item.legacy_instance_id,
        business_id=item.business_id,
        engine_id=item.engine_id,
        jurisdiction=item.jurisdiction,
    )
    approval_id = _approval_id(action_id)
    approved = db.query(LegacyOrchestrationEvent).filter(
        LegacyOrchestrationEvent.event_id == approval_id
    ).first()
    if not approved:
        _event(
            db,
            event_id=approval_id,
            legacy_instance_id=item.legacy_instance_id,
            event_type=APPROVAL_EVENT,
            message="Owner explicitly authorized internal listing-draft creation",
            payload={
                "action_id": action_id,
                "payload_sha256": hashlib.sha256(item.payload_json.encode("utf-8")).hexdigest(),
                "scope": "INTERNAL_DRAFT_ONLY",
            },
        )
    db.commit()
    return {"action_id": action_id, "status": "approved_for_internal_draft", "external_actions_allowed": False}


def _render_listing(payload: dict[str, Any]) -> str:
    """Deterministic, token-free product copy with structured metadata."""
    if payload.get("action_type") != ACTION_TYPE or payload.get("mode") != "INTERNAL_DRAFT_ONLY":
        raise ValueError("unsupported or unsafe action")
    title = payload.get("title")
    description = payload.get("description")
    cents = payload.get("price_cents_cad")
    if (
        not isinstance(title, str) or not 8 <= len(title.strip()) <= 120
        or not isinstance(description, str) or not 40 <= len(description.strip()) <= 1800
        or not isinstance(cents, int) or not 1 <= cents <= 10_000_000
    ):
        raise ValueError("invalid listing details")
    draft = {
        "commercial_status": "NOT_PUBLISHED",
        "external_effects": 0,
        "product_id": payload["product_id"],
        "business_id": payload["business_id"],
        "title": title.strip(),
        "description": description.strip(),
        "price_cents": cents,
        "currency": "CAD",
        "purchase_url": None,
        "delivery_configured": False,
        "verification_scope": "internal_media_record_only",
    }
    data = _canonical(draft)
    if len(data.encode("utf-8")) > MAX_BODY_LENGTH:
        raise ValueError("listing exceeds allowed size")
    return data


def run_one_approved_draft(db: Session) -> dict:
    """Atomically execute ONE approved internal task and persist its receipt.

    The draft and verified receipt are committed in the same database transaction.
    PostgreSQL skip_locked prevents concurrent workers from taking the same row.
    SQLite is used only in isolated single-worker tests.
    """
    queued = db.query(LegacyInstanceWorkItem).filter(
        LegacyInstanceWorkItem.status == "queued",
        LegacyInstanceWorkItem.risk_profile == "no_external_effects",
        LegacyInstanceWorkItem.integration_profile == "none",
    ).order_by(LegacyInstanceWorkItem.id.asc()).with_for_update(skip_locked=True).limit(100).all()

    last_blocked = None
    for item in queued:
        payload = _json(item.payload_json, {})
        if not isinstance(payload, dict) or payload.get("action_type") != ACTION_TYPE or payload.get("mode") != "INTERNAL_DRAFT_ONLY":
            continue
        approval = db.query(LegacyOrchestrationEvent).filter(
            LegacyOrchestrationEvent.event_id == _approval_id(item.action_id)
        ).first()
        authority = "PER_ACTION"
        mandate_id = None
        if not approval:
            mandate_id = payload.get("mandate_id")
            if not mandate_id:
                continue
            reason = _check_draft_mandate(db, item, payload)
            if reason:
                last_blocked = {"status": "blocked", "action_id": item.action_id,
                                "reason": reason, "verified": False}
                continue
            authority = "STANDING_MANDATE"
        else:
            evidence = _json(approval.payload_json, {})
            if (
                approval.event_type != APPROVAL_EVENT
                or approval.legacy_instance_id != item.legacy_instance_id
                or not isinstance(evidence, dict)
                or evidence.get("action_id") != item.action_id
                or evidence.get("scope") != "INTERNAL_DRAFT_ONLY"
                or evidence.get("payload_sha256") != hashlib.sha256(item.payload_json.encode("utf-8")).hexdigest()
            ):
                return {"status": "blocked", "action_id": item.action_id, "reason": "approval evidence mismatch", "verified": False}

        _check_legacy(
            db,
            legacy_instance_id=item.legacy_instance_id,
            business_id=item.business_id,
            engine_id=item.engine_id,
            jurisdiction=item.jurisdiction,
        )
        policy = _internal_policy_decision(db, item, approved=True)
        if policy.verdict != "ALLOW":
            return {
                "status": "blocked",
                "action_id": item.action_id,
                "verified": False,
                "reason": policy.reason,
            }
        try:
            draft_body = _render_listing(_json(item.payload_json, {}))
        except (ValueError, TypeError, KeyError) as exc:
            return {"status": "blocked", "action_id": item.action_id, "reason": str(exc), "verified": False}

        receipt_id = _receipt_id(item.action_id)
        if db.query(LegacyOrchestrationEvent).filter(
            LegacyOrchestrationEvent.event_id == receipt_id
        ).first():
            return {"status": "blocked", "action_id": item.action_id, "reason": "receipt exists for queued work; manual reconciliation required", "verified": False}

        media = MediaContent(
            title=_json(item.payload_json, {})["title"],
            content_type="product_listing_draft",
            body=draft_body,
            tags="business_factory,internal_draft",
            audience="internal",
        )
        db.add(media)
        db.flush()
        stored = db.query(MediaContent).filter(MediaContent.id == media.id).first()
        if not stored or stored.body != draft_body:
            db.rollback()
            return {"status": "blocked", "action_id": item.action_id, "reason": "artifact persistence verification failed", "verified": False}

        digest = hashlib.sha256(stored.body.encode("utf-8")).hexdigest()
        evidence = {
            "action_id": item.action_id,
            "media_content_id": stored.id,
            "sha256": digest,
            "artifact_type": stored.content_type,
            "external_effects": 0,
            "sales_verified": False,
            "verification_scope": "database_artifact_only",
            "policy_verdict": policy.verdict,
            "policy_reason": policy.reason,
            "authority_mode": authority,
            "mandate_id": mandate_id,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        _event(
            db,
            event_id=receipt_id,
            legacy_instance_id=item.legacy_instance_id,
            event_type=RECEIPT_EVENT,
            message="Internal listing draft stored and read back successfully",
            payload=evidence,
        )
        if mandate_id is not None:
            _event(db, event_id="BF-MUSE-" + hashlib.sha256(item.action_id.encode()).hexdigest(),
                   legacy_instance_id=item.legacy_instance_id, event_type=_mandate_use_type(mandate_id),
                   message="Standing mandate use committed with verified draft",
                   payload={"mandate_id": mandate_id, "action_id": item.action_id, "sha256": digest})
        item.status = "completed"
        db.commit()
        return {"status": "completed", "verified": True, "receipt": evidence}

    return last_blocked or {"status": "idle", "verified": False, "reason": "no eligible owner-approved internal tasks"}


def action_status(db: Session, action_id: str) -> dict:
    item = db.query(LegacyInstanceWorkItem).filter(
        LegacyInstanceWorkItem.action_id == action_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="action not found")
    receipt = db.query(LegacyOrchestrationEvent).filter(
        LegacyOrchestrationEvent.event_id == _receipt_id(action_id)
    ).first()
    verified = False
    evidence = _json(receipt.payload_json, {}) if receipt else None
    if receipt and evidence:
        media = db.query(MediaContent).filter(
            MediaContent.id == evidence.get("media_content_id")
        ).first()
        verified = (
            item.status == "completed"
            and bool(media)
            and media.content_type == "product_listing_draft"
            and hashlib.sha256(media.body.encode("utf-8")).hexdigest() == evidence.get("sha256")
        )
    return {
        "action_id": action_id,
        "status": item.status,
        "internal_artifact_verified": verified,
        "receipt": evidence if verified else None,
        "externally_published": False,
        "payment_verified": False,
    }
