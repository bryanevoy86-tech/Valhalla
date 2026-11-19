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

    for item in queued:
        approval = db.query(LegacyOrchestrationEvent).filter(
            LegacyOrchestrationEvent.event_id == _approval_id(item.action_id)
        ).first()
        if not approval:
            continue
        evidence = _json(approval.payload_json, {})
        if (
            evidence.get("scope") != "INTERNAL_DRAFT_ONLY"
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
        item.status = "completed"
        db.commit()
        return {"status": "completed", "verified": True, "receipt": evidence}

    return {"status": "idle", "verified": False, "reason": "no eligible owner-approved internal tasks"}


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
