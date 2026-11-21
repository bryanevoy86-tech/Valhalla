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
from uuid import UUID

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.loki.models import LokiFinding, LokiIndependentReceipt, LokiReconsideration, LokiReview
from app.loki.review_service import verdict as independent_verdict
from app.models.god_verdicts import GodVerdict
from app.models.completion_registry import (
    LegacyInstanceRegistryItem,
    LegacyInstanceWorkItem,
    LegacyOrchestrationEvent,
)
from app.models.media_engine import MediaContent
from app.services.specialist_triggers import publish_verified_outcome
from app.services.product_artifacts import artifact_reference, load_artifact, require_artifact_schema, verify_artifact
from app.core.autonomy_governor import require_internal_draft
from sqlalchemy import func, inspect
from sqlalchemy.exc import IntegrityError


ACTION_TYPE = "draft_product_listing_v1"
APPROVAL_EVENT = "FACTORY_OWNER_APPROVED"
RECEIPT_EVENT = "FACTORY_ARTIFACT_VERIFIED"
MIMIR_OUTCOME_EVENT = "MIMIR_INTERNAL_ARTIFACT_VERIFIED"
MAX_BODY_LENGTH = 5000


def require_factory_key(
    provided: str | None = Header(default=None, alias="X-Business-Factory-Key"),
) -> None:
    """Admin-only; missing configuration must deny all API access."""
    expected = os.environ.get("VALHALLA_FACTORY_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Business Factory admin key not configured")
    if not provided or not hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8")):
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


def _mimir_outcome_id(action_id: str) -> str:
    return "MIMIR-" + hashlib.sha256(action_id.encode()).hexdigest()


def _mimir_outcome(item: LegacyInstanceWorkItem, receipt: dict) -> dict:
    outcome = {
        "action_id": item.action_id,
        "receipt_event_id": _receipt_id(item.action_id),
        "artifact_sha256": receipt["sha256"],
        "legacy_instance_id": item.legacy_instance_id,
        "business_id": item.business_id,
        "engine_id": item.engine_id,
        "jurisdiction": item.jurisdiction,
        "observed_at": receipt["verified_at"],
        "evidence_scope": "INTERNAL_ARTIFACT_ONLY",
        "sales_verified": False,
    }
    if "product_asset" in receipt:
        outcome["product_asset"] = receipt["product_asset"]
    if "prime_decision" in receipt:
        outcome["prime_decision"] = receipt["prime_decision"]
    return outcome


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
    businesses = _json(row.assigned_businesses_json, [])
    jurisdictions = _json(row.assigned_jurisdictions_json, [])
    engines = _json(row.engines_json, [])
    if any(not isinstance(values, list) or any(not isinstance(v, str) for v in values)
           for values in (businesses, jurisdictions, engines)):
        raise HTTPException(status_code=409, detail="invalid legacy scope registry")
    if (
        context.get("jurisdiction") != jurisdiction
        or context.get("business_id") != business_id
        or business_id not in businesses
        or jurisdiction not in jurisdictions
        or engine_id not in engines
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


def _listing_asset(db: Session, artifact_id: UUID, work: Any, product_id: str, *, lock: bool = False) -> dict:
    require_artifact_schema(db)
    asset = load_artifact(db, artifact_id, lock=lock)
    if asset.product_id != product_id or any(
        getattr(asset, key) != getattr(work, key)
        for key in ("legacy_instance_id", "business_id", "engine_id", "jurisdiction")
    ):
        raise HTTPException(status_code=409, detail="Product artifact does not match the listing scope")
    verify_artifact(asset)
    return artifact_reference(asset)


def _bound_prime_decision(db: Session, verdict_id: UUID, work: Any, listing: dict) -> dict:
    asset = listing.get("product_asset")
    if not isinstance(asset, dict):
        raise HTTPException(status_code=422, detail="A governed listing requires an exact product asset")
    schema = inspect(db.connection())
    if any(not schema.has_table(model.__tablename__) for model in (
        GodVerdict, LokiReview, LokiIndependentReceipt, LokiFinding, LokiReconsideration,
    )):
        raise HTTPException(status_code=503, detail="Prime decision evidence schema not ready")
    snapshot = db.get(GodVerdict, verdict_id)
    if not snapshot or snapshot.trigger != "phase3_universal_opportunity":
        raise HTTPException(status_code=409, detail="A live Prime decision snapshot is required")
    metadata = snapshot.metadata_json
    if (not isinstance(metadata, dict) or metadata.get("shadow_mode") is not False
            or metadata.get("internal_draft_eligible") is not True):
        raise HTTPException(status_code=409, detail="Prime did not recommend an eligible internal draft")
    try:
        independent = metadata["owner_approval_envelope"]["independent_loki"]
        review = db.get(LokiReview, UUID(independent["review_id"]))
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise HTTPException(status_code=409, detail="Prime snapshot has no independent Loki receipt") from exc
    if not review or review.artifact_type != "universal_opportunity":
        raise HTTPException(status_code=409, detail="Independent Loki proposal is missing")
    decision = independent_verdict(db, review)
    if not decision.ok_to_proceed or decision.artifact_sha256 != independent.get("artifact_sha256"):
        raise HTTPException(status_code=409, detail="Independent Loki reconsideration is required")
    proposal = review.raw_input
    specialist_inputs = proposal.get("specialist_inputs") if isinstance(proposal, dict) else None
    expected = {
        "product_id": listing["product_id"], "title": listing["title"],
        "description": listing["description"], "price_cents_cad": listing["price_cents_cad"],
        "artifact_id": asset["artifact_id"], "artifact_sha256": asset["sha256"], "industry": work.industry,
    }
    if (
        not isinstance(specialist_inputs, dict)
        or proposal.get("opportunity_id") != metadata.get("opportunity_id")
        or proposal.get("simulation_fixture") is not False
        or proposal.get("legacy") != work.legacy_instance_id
        or proposal.get("engine_id") != work.engine_id
        or proposal.get("jurisdiction") != work.jurisdiction
        or specialist_inputs.get("business_id") != work.business_id
        or _canonical(specialist_inputs.get("proposed_internal_listing")) != _canonical(expected)
    ):
        raise HTTPException(status_code=409, detail="Listing differs from the reviewed Prime proposal")
    return {
        "verdict_id": str(verdict_id), "review_id": str(review.id),
        "proposal_sha256": decision.artifact_sha256,
    }


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
    if (asset_id := getattr(request, "artifact_id", None)) is not None:
        inputs["product_asset"] = _listing_asset(db, asset_id, request, request.product_id)
    if (verdict_id := getattr(request, "prime_verdict_id", None)) is not None:
        inputs["prime_decision"] = _bound_prime_decision(db, verdict_id, request, inputs)
    key_hash = hashlib.sha256(
        f"{request.legacy_instance_id}:{request.request_key}".encode("utf-8")
    ).hexdigest()
    action_id = "bfd_" + key_hash[:32]
    idem_key = "bfv1_" + key_hash

    def existing_submission():
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
        return None

    duplicate = existing_submission()
    if duplicate is not None:
        return duplicate

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
    try:
        db.commit()
    except IntegrityError:
        # Another submitter may have won the unique-key race. Roll back both
        # work and queue event, then verify the winner's complete request.
        db.rollback()
        duplicate = existing_submission()
        if duplicate is None:
            raise
        return duplicate
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
    if "product_asset" in payload:
        draft["product_asset"] = payload["product_asset"]
    if "prime_decision" in payload:
        draft["prime_decision"] = payload["prime_decision"]
    data = _canonical(draft)
    if len(data.encode("utf-8")) > MAX_BODY_LENGTH:
        raise ValueError("listing exceeds allowed size")
    return data


def _execute_locked_draft(db: Session, item: LegacyInstanceWorkItem) -> dict | None:
    """Execute a single locked row; caller rolls back unsuccessful attempts."""
    payload = _json(item.payload_json, {})
    if not isinstance(payload, dict) or payload.get("action_type") != ACTION_TYPE or payload.get("mode") != "INTERNAL_DRAFT_ONLY":
        return None
    if payload.get("business_id") != item.business_id:
        return {"status": "blocked", "action_id": item.action_id,
                "reason": "work payload business mismatch", "verified": False}
    approval = db.query(LegacyOrchestrationEvent).filter(
        LegacyOrchestrationEvent.event_id == _approval_id(item.action_id)
    ).first()
    authority = "PER_ACTION"
    mandate_id = None
    if not approval:
        mandate_id = payload.get("mandate_id")
        if not mandate_id:
            return None
        reason = _check_draft_mandate(db, item, payload)
        if reason:
            return {"status": "blocked", "action_id": item.action_id,
                            "reason": reason, "verified": False}
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

    try:
        _check_legacy(
            db,
            legacy_instance_id=item.legacy_instance_id,
            business_id=item.business_id,
            engine_id=item.engine_id,
            jurisdiction=item.jurisdiction,
        )
    except HTTPException as exc:
        return {"status": "blocked", "action_id": item.action_id,
                "reason": str(exc.detail), "verified": False}
    if "product_asset" in payload:
        try:
            ref = payload["product_asset"]
            asset = _listing_asset(db, UUID(ref["artifact_id"]), item, payload["product_id"], lock=True)
            if asset != ref:
                raise HTTPException(status_code=409, detail="Product artifact replaced since submission")
        except (TypeError, ValueError, KeyError, HTTPException) as exc:
            return {
                "status": "blocked", "action_id": item.action_id, "verified": False,
                "reason": str(exc.detail) if isinstance(exc, HTTPException) else "Invalid product artifact reference",
            }
    if "prime_decision" in payload:
        try:
            ref = payload["prime_decision"]
            if _bound_prime_decision(db, UUID(ref["verdict_id"]), item, payload) != ref:
                raise HTTPException(status_code=409, detail="Prime decision evidence mismatch")
        except (TypeError, ValueError, KeyError, HTTPException) as exc:
            return {
                "status": "blocked", "action_id": item.action_id, "verified": False,
                "reason": str(exc.detail) if isinstance(exc, HTTPException) else "Invalid Prime decision reference",
            }
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
    if "product_asset" in payload:
        evidence["product_asset"] = payload["product_asset"]
    if "prime_decision" in payload:
        evidence["prime_decision"] = payload["prime_decision"]
    _event(
        db,
        event_id=receipt_id,
        legacy_instance_id=item.legacy_instance_id,
        event_type=RECEIPT_EVENT,
        message="Internal listing draft stored and read back successfully",
        payload=evidence,
    )
    outcome_event_id = _mimir_outcome_id(item.action_id)
    _event(
        db,
        event_id=outcome_event_id,
        legacy_instance_id=item.legacy_instance_id,
        event_type=MIMIR_OUTCOME_EVENT,
        message="Verified internal outcome for Mimir",
        payload=_mimir_outcome(item, evidence),
    )
    publish_verified_outcome(db, {
        "legacy_instance_id": item.legacy_instance_id, "business_id": item.business_id,
        "engine_id": item.engine_id, "jurisdiction": item.jurisdiction,
    }, outcome_event_id)
    if mandate_id is not None:
        _event(db, event_id="BF-MUSE-" + hashlib.sha256(item.action_id.encode()).hexdigest(),
               legacy_instance_id=item.legacy_instance_id, event_type=_mandate_use_type(mandate_id),
               message="Standing mandate use committed with verified draft",
               payload={"mandate_id": mandate_id, "action_id": item.action_id, "sha256": digest})
    item.status = "completed"
    db.commit()
    return {"status": "completed", "verified": True, "receipt": evidence}



def run_one_approved_draft(db: Session) -> dict:
    """Complete at most one authorized internal draft in an owned worker session.

    Snapshot a high-water mark so concurrent arrivals cannot extend this pass
    indefinitely. Lock one work row at a time; release skipped/blocked rows and
    mandate locks before looking farther down the queue. No provider effects.
    Call only with a dedicated session containing no unrelated pending writes.
    """
    lane = (
        LegacyInstanceWorkItem.status == "queued",
        LegacyInstanceWorkItem.risk_profile == "no_external_effects",
        LegacyInstanceWorkItem.integration_profile == "none",
    )
    last_blocked = None
    cursor = 0
    try:
        ceiling = db.query(func.max(LegacyInstanceWorkItem.id)).filter(*lane).scalar()
        while ceiling is not None and cursor < ceiling:
            item = db.query(LegacyInstanceWorkItem).filter(
                *lane, LegacyInstanceWorkItem.id > cursor,
                LegacyInstanceWorkItem.id <= ceiling,
            ).order_by(LegacyInstanceWorkItem.id.asc()).with_for_update(skip_locked=True).first()
            if item is None:
                break
            cursor = item.id
            result = _execute_locked_draft(db, item)
            if result is not None and result["status"] == "completed":
                return result
            # No effect was verified. Release row/mandate locks and discard
            # any uncommitted artifact rather than block unrelated businesses.
            db.rollback()
            if result is not None:
                last_blocked = result
                if result.get("reason") == "EMERGENCY_STOP_ACTIVE":
                    return result
        db.rollback()
    except Exception:
        db.rollback()
        raise
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
    # A matching hash alone does not bind an artifact to this action or Legacy.
    # Reject malformed and contradictory evidence before looking up the artifact.
    if (
        item.status == "completed"
        and receipt is not None
        and receipt.event_type == RECEIPT_EVENT
        and receipt.legacy_instance_id == item.legacy_instance_id
        and isinstance(evidence, dict)
        and evidence.get("action_id") == item.action_id
        and evidence.get("artifact_type") == "product_listing_draft"
        and evidence.get("verification_scope") == "database_artifact_only"
        and type(evidence.get("external_effects")) is int
        and evidence["external_effects"] == 0
        and evidence.get("sales_verified") is False
        and type(evidence.get("media_content_id")) is int
        and evidence["media_content_id"] > 0
        and isinstance(evidence.get("sha256"), str)
    ):
        payload = _json(item.payload_json, {})
        expected_body = None
        if (isinstance(payload, dict) and payload.get("business_id") == item.business_id
                and payload.get("product_asset") == evidence.get("product_asset")
                and payload.get("prime_decision") == evidence.get("prime_decision")):
            try:
                expected_body = _render_listing(payload)
            except (ValueError, TypeError, KeyError):
                pass
        media = db.query(MediaContent).filter(
            MediaContent.id == evidence["media_content_id"]
        ).first()
        verified = (
            expected_body is not None
            and media is not None
            and media.content_type == "product_listing_draft"
            and isinstance(media.body, str)
            and media.body == expected_body
            and hashlib.sha256(media.body.encode("utf-8")).hexdigest() == evidence["sha256"]
        )
    return {
        "action_id": action_id,
        "status": item.status,
        "internal_artifact_verified": verified,
        "receipt": evidence if verified else None,
        "externally_published": False,
        "payment_verified": False,
    }



def verified_internal_outcomes(
    db: Session, *, legacy_instance_id: str, business_id: str, engine_id: str, jurisdiction: str, limit: int = 20,
) -> list[dict]:
    """Project durable facts only after re-reading their scoped source receipt."""
    items = (
        db.query(LegacyInstanceWorkItem)
        .filter_by(
            status="completed", legacy_instance_id=legacy_instance_id,
            business_id=business_id, engine_id=engine_id, jurisdiction=jurisdiction,
        )
        .order_by(LegacyInstanceWorkItem.updated_at.desc(), LegacyInstanceWorkItem.id.desc())
        .limit(limit)
        .all()
    )
    outcomes = []
    for item in items:
        event_id = _mimir_outcome_id(item.action_id)
        event = db.query(LegacyOrchestrationEvent).filter_by(
            event_id=event_id, event_type=MIMIR_OUTCOME_EVENT, legacy_instance_id=legacy_instance_id,
        ).one_or_none()
        if event is None:
            continue
        current = action_status(db, item.action_id)
        if not current["internal_artifact_verified"] or not isinstance(current["receipt"].get("verified_at"), str):
            continue
        expected = _mimir_outcome(item, current["receipt"])
        if _json(event.payload_json, {}) == expected:
            outcomes.append({"outcome_event_id": event_id, **expected})
    return outcomes
