"""One disposable operating loop over existing Foundry and treasury operations."""
from datetime import date, datetime, timezone
import hashlib
import os
from typing import Annotated, Literal
from uuid import UUID, uuid5

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from pydantic import Field, ValidationError
from sqlalchemy import inspect, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.core.runtime_flags import is_sandbox
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyInstanceWorkItem as Work, LegacyOrchestrationEvent as Event
from app.models.foundry_checkout import FoundryFixtureSettlement, FoundryRehearsalOrder, FoundryRehearsalPayment
from app.models.go_live_state import GoLiveState
from app.models.treasury_reconciliation import StatementImport
from app.providers.stripe_adapter import verify_stripe_signature
from app.routers import foundry_checkout as checkout
from app.routers.auth_weweb import get_current_user
from app.routers.economic_control import _performance
from app.routers.prime_business_factory import DraftMandateRequest, ListingDraftRequest
from app.routers.research_participant import profile
from app.schemas.economic_control import Performance
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.economic_control import require_no_containment
from app.services.prime_business_execution import (
    _bound_prime_decision, _check_legacy, _emergency_stop_active, _event, _execute_locked_draft, _json,
    _lock_mandate, _mandate_revocation_id, _prepare_draft_mandate, action_status, submit_listing_draft,
    verify_mimir_claims, require_owner_mandate_key,
)
from app.services.treasury_reconciliation import StatementFixture, append_statement, statement_ready

router = APIRouter(prefix="/api/foundry/operating-rehearsal", tags=["foundry-operating-rehearsal"])
EVENT = "FOUNDRY_OPERATING_REHEARSAL"
ACTORS = {
    "mandate": "OWNER_AUTHORITY", "listing": "PRIME_WORKER", "enrolled": "BUYER_SESSION",
    "purchase": "BUYER_SESSION", "order": "PRIME_WORKER", "capture": "SIGNED_PAYMENT_FIXTURE",
    "delivery": "PRIME_WORKER", "acknowledge": "BUYER_SESSION", "support": "BUYER_SESSION",
    "refund_requested": "PRIME_WORKER", "refund": "SIGNED_PAYMENT_FIXTURE",
    "statement": "SIGNED_BANK_FIXTURE", "outcome": "PRIME_WORKER",
}
PREVIOUS = {
    "enrolled": "listing", "purchase": "enrolled", "capture": "order", "acknowledge": "delivery",
    "support": "acknowledge", "refund": "refund_requested", "statement": "refund",
}
Sha = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class Mandate(StrictModel):
    listing: ListingDraftRequest
    campaign_id: Annotated[int, Field(strict=True, gt=0)]
    buyer_id: Annotated[int, Field(strict=True, gt=0)]
    terms_sha256: Sha
    cost_minor: Annotated[int, Field(strict=True, gt=0, le=100_000)]
    ttl_seconds: Annotated[int, Field(strict=True, ge=60, le=86400)]


class BuyerInput(StrictModel):
    action: Literal["enrolled", "purchase", "acknowledge", "support"]
    sha256: Sha


def enabled():
    return (is_sandbox() and os.getenv("VALHALLA_FOUNDRY_OPERATING_REHEARSAL") == "1"
            and os.getenv("APP_ENV", "").lower() in {"dev", "test", "sandbox"}
            and os.getenv("ENV", "").lower() in {"", "dev", "test", "sandbox"})


def guard(db):
    if not enabled():
        raise HTTPException(503, "Disposable operating rehearsal disabled")
    if (not inspect(db.connection()).has_table(GoLiveState.__tablename__)
            or _emergency_stop_active(db)):
        raise HTTPException(503, "Operating rehearsal stopped")
    release = db.get(GoLiveState, 1)
    if release is not None and release.go_live_enabled:
        raise HTTPException(503, "Operating rehearsal cannot run with go-live enabled")
    checkout.schema(db)


def event_key(run_id, phase):
    return f"FOP-{run_id.hex}-{phase}"


def run_ref(run_id, label):
    return uuid5(run_id, label)


def add_receipt(db, run_id, phase, scope, evidence, previous):
    ref = event_key(run_id, phase)
    body = jsonable_encoder({"scope": scope, "phase": phase, "actor": ACTORS[phase],
                             "evidence": evidence, "previous_sha256": previous, "external_effects": 0})
    body["sha256"] = artifact_digest("foundry_operating_rehearsal", ref, body)
    _event(db, event_id=ref, legacy_instance_id=scope["legacy_instance_id"], event_type=EVENT, message=phase, payload=body)
    return body


def read_run(db, run_id):
    rows = db.scalars(select(Event).where(Event.event_id.startswith(f"FOP-{run_id.hex}-")).order_by(Event.id)).all()
    if not rows:
        raise HTTPException(404, "Operating rehearsal unavailable")
    chain = {}
    previous = None
    phases = tuple(ACTORS)
    for index, row in enumerate(rows):
        body = _json(row.payload_json, {})
        if not isinstance(body, dict) or index >= len(phases):
            raise HTTPException(409, "Operating rehearsal receipt integrity failed")
        digest = body.pop("sha256", None)
        phase, scope = body.get("phase"), body.get("scope")
        if (phase != phases[index] or row.event_id != event_key(run_id, phase)
                or row.event_type != EVENT or not isinstance(scope, dict) or row.legacy_instance_id != scope.get("legacy_instance_id")
                or body.get("actor") != ACTORS[phase] or body.get("external_effects") != 0
                or body.get("previous_sha256") != previous
                or digest != artifact_digest("foundry_operating_rehearsal", row.event_id, body)
                or (chain and scope != chain["mandate"]["scope"])):
            raise HTTPException(409, "Operating rehearsal receipt integrity failed")
        chain[phase] = {**body, "sha256": digest}
        previous = digest
    return chain


def active(db, run_id):
    guard(db)
    # Take the first write lock before reading state, including on disposable SQLite.
    db.execute(update(Event).where(Event.event_id == event_key(run_id, "mandate")).values(message=Event.message))
    chain = read_run(db, run_id)
    mandate = chain["mandate"]["evidence"]
    scope = chain["mandate"]["scope"]
    grant = _lock_mandate(db, mandate["listing"]["mandate_id"])
    revoked = db.scalar(select(Event.id).filter_by(event_id=_mandate_revocation_id(mandate["listing"]["mandate_id"])))
    if (grant is None or revoked is not None or mandate["grant"] != _json(grant.payload_json, {})
            or mandate["grant"]["expires_at_epoch"] <= datetime.now(timezone.utc).timestamp()):
        raise HTTPException(409, "Operating rehearsal mandate expired or revoked")
    _check_legacy(db, **scope, lock=True)
    if "outcome" not in chain:
        require_no_containment(db, scope)
    plan = checkout.read_plan(db, mandate["campaign_id"], scope)
    if not plan or plan["sha256"] != mandate["plan_sha256"]:
        raise HTTPException(409, "Acquisition plan changed")
    checkout._require_current_campaign_plan(db, mandate["campaign_id"], plan)
    listing = ListingDraftRequest.model_validate(mandate["listing"])
    reference = review_listing(db, listing)
    if reference != mandate["prime_decision"]:
        raise HTTPException(409, "Prime decision evidence changed")
    return chain, mandate, scope


def review_listing(db, listing):
    asset = checkout.load_artifact(db, listing.artifact_id, lock=True)
    return _bound_prime_decision(db, listing.prime_verdict_id, listing, {
        **listing.model_dump(), "product_asset": {"artifact_id": str(asset.id), "sha256": asset.sha256},
    })


def commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Concurrent or conflicting operating receipt") from None


def save(db, run_id, chain, phase, evidence):
    if phase in chain:
        if chain[phase]["evidence"] != jsonable_encoder(evidence):
            raise HTTPException(409, "Operating rehearsal input changed on replay")
        return chain[phase]
    if phase != tuple(ACTORS)[len(chain)]:
        raise HTTPException(409, "Operating transition is out of sequence")
    receipt = add_receipt(db, run_id, phase, chain["mandate"]["scope"], evidence, next(reversed(chain.values()))["sha256"])
    commit(db)
    return receipt


@router.post("/{run_id}/mandate", dependencies=[Depends(require_prime_control_key), Depends(require_owner_mandate_key)])
def mandate(run_id: UUID, request: Mandate, db: Session = Depends(get_db)):
    guard(db)
    listing = request.listing
    if not listing.artifact_id or not listing.prime_verdict_id or listing.mandate_id:
        raise HTTPException(422, "An exact reviewed listing is required")
    listing = listing.model_copy(update={"mandate_id": f"op-{run_id.hex}", "request_key": run_id.hex})
    scope = MarketScope.model_validate({name: getattr(listing, name) for name in MarketScope.model_fields}).model_dump()
    _check_legacy(db, **scope, lock=True)
    require_no_containment(db, scope)
    profile(db, request.buyer_id)
    plan = checkout.read_plan(db, request.campaign_id, scope)
    if not plan or plan["request"]["channel"] != "DIRECT_OPT_IN":
        raise HTTPException(409, "An approved opt-in campaign plan is required")
    checkout._require_current_campaign_plan(db, request.campaign_id, plan)
    decision = review_listing(db, listing)
    if db.scalar(select(Event.id).filter_by(event_id=event_key(run_id, "mandate"))):
        raise HTTPException(409, "Operating rehearsal ID already used")
    grant = _prepare_draft_mandate(db, DraftMandateRequest(
        **scope, mandate_id=listing.mandate_id, product_id=listing.product_id, ttl_seconds=request.ttl_seconds,
        max_uses=1, max_price_cents_cad=listing.price_cents_cad,
    ))
    result = add_receipt(db, run_id, "mandate", scope, {
        **request.model_dump(mode="json"), "listing": listing.model_dump(mode="json"), "grant": grant,
        "plan_sha256": plan["sha256"], "prime_decision": decision,
    }, None)
    commit(db)
    return {"phase": result["phase"], "sha256": result["sha256"], "external_effects": 0}


def check_buyer(db, session, mandate):
    user = profile(db, session.get("user_id"))
    if user.user_id != mandate["buyer_id"] or user.email != session.get("sub"):
        raise HTTPException(404, "Operating rehearsal unavailable")


@router.post("/{run_id}/buyer")
def buyer(run_id: UUID, request: BuyerInput, session: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    chain, mandate, _ = active(db, run_id)
    check_buyer(db, session, mandate)
    previous = chain.get(PREVIOUS[request.action])
    if previous is None:
        raise HTTPException(409, "Previous operating step is required")
    expected = (chain["delivery"]["evidence"]["artifact_sha256"] if request.action == "acknowledge"
                else chain["acknowledge"]["sha256"] if request.action == "support" else mandate["terms_sha256"])
    if request.sha256 != expected:
        raise HTTPException(409, "Buyer evidence differs from the authorized step")
    if "refund" in chain and request.action != "support":
        raise HTTPException(409, "Buyer delivery is no longer available")
    return save(db, run_id, chain, request.action, {"buyer_id": mandate["buyer_id"], "input_sha256": expected})


@router.get("/{run_id}/delivery")
def delivery(run_id: UUID, session: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    chain, mandate, _ = active(db, run_id)
    check_buyer(db, session, mandate)
    if "delivery" not in chain or "refund" in chain:
        raise HTTPException(404, "Operating rehearsal delivery unavailable")
    _, asset, _, _ = checkout._listing(db, chain["listing"]["evidence"]["action_id"])
    return Response(asset.data, media_type="application/octet-stream", headers={
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "X-Artifact-SHA256": asset.sha256,
    })


@router.post("/{run_id}/payment")
async def payment(run_id: UUID, request: Request, db: Session = Depends(get_db)):
    guard(db)
    if os.getenv("VALHALLA_FOUNDRY_FIXTURE_SECRET") in {
        os.getenv("VALHALLA_OPERATING_FIXTURE_BANK_SECRET"), os.getenv("VALHALLA_LOKI_REVIEWER_KEY"),
    }:
        raise HTTPException(503, "Independent fixture payment signer unavailable")
    event = await checkout._signed_fixture(request)
    chain, _, _ = active(db, run_id)
    kind, event_id, reference, _, digest = event
    phase = "capture" if kind == "payment_intent.succeeded" else "refund"
    if (reference != f"pi_fixture_{run_id.hex}" or event_id != f"evt_fixture_{run_id.hex}_{phase}"
            or PREVIOUS[phase] not in chain):
        raise HTTPException(409, "Payment fixture differs from the requested transition")
    evidence = {"event_id": event_id, "payment_sha256": digest}
    if phase not in chain:
        order = db.get(FoundryRehearsalOrder, run_ref(run_id, "order"))
        if order is None or event[3] != order.amount_minor:
            raise HTTPException(409, "Only an exact full capture or refund is authorized")
        if db.get(FoundryRehearsalPayment, event_id) is not None:
            raise HTTPException(409, "Payment was applied outside the operating rehearsal")
        checkout._apply_fixture(event, db, commit=False)
    return save(db, run_id, chain, phase, evidence)


async def bank_document(request: Request, maximum=8192):
    secret = os.getenv("VALHALLA_OPERATING_FIXTURE_BANK_SECRET")
    if not secret or secret in {os.getenv(k) for k in (
        "VALHALLA_FOUNDRY_FIXTURE_SECRET", "VALHALLA_PRIME_CONTROL_KEY", "VALHALLA_OWNER_MANDATE_KEY",
        "VALHALLA_LOKI_REVIEWER_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_SECRET_KEY",
    )}:
        raise HTTPException(503, "Independent fixture bank signer unavailable")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > maximum:
            raise HTTPException(413, "Bank statement fixture exceeds the byte limit")
        body.extend(chunk)
    raw = bytes(body)
    if not verify_stripe_signature(raw, request.headers.get("Fixture-Bank-Signature"), secret):
        raise HTTPException(400, "Bank fixture signature invalid")
    try:
        return StatementFixture.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
    except ValidationError:
        raise HTTPException(422, "Bank fixture statement invalid") from None


@router.post("/{run_id}/statement")
async def statement(run_id: UUID, request: Request, db: Session = Depends(get_db)):
    guard(db)
    document, digest = await bank_document(request)
    chain, mandate, scope = active(db, run_id)
    amount = mandate["listing"]["price_cents_cad"]
    if ("refund" not in chain or document.id != run_ref(run_id, "statement") or document.scope.model_dump() != scope
            or document.source_id != "fixture:operating-bank" or document.account_ref != f"fixture:{run_id.hex}"
            or document.purpose != "BUSINESS" or document.currency != "CAD"
            or document.opening_minor != 0 or document.closing_minor != 0 or document.outstanding_liabilities_minor != 0
            or document.expense_budget_minor != 0
            or {x.external_ref: (x.amount_minor, x.category) for x in document.entries} != {
                f"evt_fixture_{run_id.hex}_capture": (amount, "TRANSFER"),
                f"evt_fixture_{run_id.hex}_refund": (-amount, "TRANSFER"),
            }):
        raise HTTPException(409, "Statement is outside the signed operating run")
    if not statement_ready(db):
        raise HTTPException(503, "Statement fixture schema unavailable")
    if "statement" not in chain and db.get(StatementImport, document.id) is not None:
        raise HTTPException(409, "Statement was imported outside the operating rehearsal")
    record = append_statement(db, document, datetime.now(timezone.utc).date())
    return save(db, run_id, chain, "statement", {"statement_id": document.id, "statement_sha256": record["sha256"],
                                                 "signed_payload_sha256": digest,
                                                 "start": document.start, "end": document.end})


def finish(db, run_id, chain, mandate, scope, order_id):
    document = chain["statement"]["evidence"]
    for phase in ("capture", "refund"):
        event_id = chain[phase]["evidence"]["event_id"]
        if db.get(FoundryFixtureSettlement, event_id) is not None:
            raise HTTPException(409, "Settlement was matched outside the operating rehearsal")
        result = checkout._reconcile_settlement(order_id, checkout.SettlementIn(
            statement_id=document["statement_id"], entry_ref=event_id, payment_event_id=event_id,
        ), db, commit=False)
        if (result["status"] != "MATCHED_FIXTURE" or result["statement_sha256"] != document["statement_sha256"]
                or result["payment_sha256"] != chain[phase]["evidence"]["payment_sha256"]):
            raise HTTPException(409, "Signed statement does not reconcile")
    order = db.get(FoundryRehearsalOrder, order_id, with_for_update=True)
    if checkout._rehearsal_costs(db, order):
        raise HTTPException(409, "Expenses were recorded outside the operating rehearsal")
    checkout._record_cost(order_id, checkout.CostIn(
        fixture_ref=f"fixture:{run_id.hex}", category="FULFILLMENT", amount_minor=mandate["cost_minor"],
    ), db, commit=False)
    if checkout._support_resolution(db, order) is not None:
        raise HTTPException(409, "Support was resolved outside the operating rehearsal")
    checkout._record_support_resolution(db, order, "Reconciled full signed refund in the disposable checkout.",
                                        routine_scope=scope, commit=False)
    proof = checkout.closed_checkout_proof(db, order_id, scope=scope)
    performance = _performance(Performance(
        id=run_ref(run_id, "performance"), scope=MarketScope.model_validate(scope),
        start=date.fromisoformat(document["start"]), end=date.fromisoformat(document["end"]),
        operating_receipts=proof["net_minor"], operating_costs=proof["fixture_cost_minor"],
        outstanding_exposure=0, uncommitted_local_cash=0, receipt_ref=f"checkout-fixture:{order_id}",
        obligations_status="SATISFIED", evidence_class="RECONCILIATION_FIXTURE", checkout_order_id=order_id,
        checkout_sha256=proof["sha256"],
    ), db, durable=False)
    evidence = {"basis": "ECONOMIC_PERFORMANCE_FIXTURE", "record_id": str(performance["id"]),
                "sha256": performance["sha256"], "period_net_minor": proof["fixture_contribution_minor"]}
    return {"mimir_claim": verify_mimir_claims(db, scope, [evidence])[0],
            "support_receipt": proof["support_resolution"]["event_id"], "checkout_sha256": proof["sha256"],
            "outstanding_obligation_minor": 0, "uncommitted_cash_minor": 0, "commercial_revenue_verified": False}


@router.post("/{run_id}/advance", dependencies=[Depends(require_prime_control_key)])
def advance(run_id: UUID, db: Session = Depends(get_db)):
    chain, mandate, scope = active(db, run_id)
    order_id = run_ref(run_id, "order")
    if "outcome" in chain:
        claim = chain["outcome"]["evidence"]["mimir_claim"]
        verify_mimir_claims(db, scope, [{k: claim[k] for k in ("basis", "record_id", "sha256", "period_net_minor")}])
        return {"status": "completed", "receipt": chain["outcome"]}
    if "listing" not in chain:
        listing = ListingDraftRequest.model_validate(mandate["listing"])
        queued = submit_listing_draft(db, listing, commit=False)
        if queued["duplicate"]:
            raise HTTPException(409, "Operating rehearsal cannot claim a foreign checkout dispatch")
        action_id = queued["action_id"]
        work = db.scalar(select(Work).filter_by(action_id=action_id).with_for_update())
        result = _execute_locked_draft(db, work, commit=False)
        if not result or result["status"] != "completed":
            raise HTTPException(409, "Scoped Factory dispatch held")
        phase, evidence = "listing", {"action_id": action_id, "listing_sha256": result["receipt"]["sha256"],
                                      "prime_decision": result["receipt"]["prime_decision"]}
    elif "order" not in chain and "purchase" in chain:
        if db.get(FoundryRehearsalOrder, order_id) is not None:
            raise HTTPException(409, "Order was created outside the operating rehearsal")
        visit = run_ref(run_id, "visit")
        if db.get(checkout.FoundryCampaignVisit, visit) is not None:
            raise HTTPException(409, "Attribution was recorded outside the operating rehearsal")
        checkout._record_campaign_visit(checkout.VisitIn(
            **scope, campaign_id=mandate["campaign_id"], visit_id=visit,
            consent_fixture_id=run_ref(run_id, "consent"),
        ), db, commit=False)
        view = checkout._create_order(checkout.OrderIn(order_id=order_id, action_id=chain["listing"]["evidence"]["action_id"],
                                      payment_reference=f"pi_fixture_{run_id.hex}", visit_id=visit), db, commit=False)
        phase, evidence = "order", {"order_id": order_id, "visit_id": visit, "price_minor": view["price_minor"]}
    elif "delivery" not in chain and "capture" in chain:
        order = db.get(FoundryRehearsalOrder, order_id, with_for_update=True)
        if order is None or order.delivered_at is not None:
            raise HTTPException(409, "Delivery is missing or was recorded outside the operating rehearsal")
        checkout._record_delivery(order_id, db, commit=False)
        phase, evidence = "delivery", {"order_id": order_id, "artifact_sha256": order.artifact_sha256}
    elif "refund_requested" not in chain and "support" in chain:
        phase, evidence = "refund_requested", {"order_id": order_id, "amount_minor": mandate["listing"]["price_cents_cad"],
                                              "provider": "LOCAL_SIGNED_FIXTURE"}
    elif "statement" in chain:
        phase, evidence = "outcome", finish(db, run_id, chain, mandate, scope, order_id)
    else:
        phase = next((name for name in ("enrolled", "purchase", "capture", "acknowledge", "support", "refund", "statement") if name not in chain), "worker")
        return {"status": "waiting", "reason": phase}
    return {"status": "advanced", "receipt": save(db, run_id, chain, phase, evidence)}


@router.get("/{run_id}", dependencies=[Depends(require_prime_control_key)])
def receipts(run_id: UUID, db: Session = Depends(get_db)):
    if not enabled():
        raise HTTPException(503, "Disposable operating rehearsal disabled")
    return {"receipts": list(read_run(db, run_id).values()), "commercial_activation_authorized": False}
