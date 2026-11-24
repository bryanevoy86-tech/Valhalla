"""One disposable operating loop over existing Foundry and treasury operations."""
from datetime import date, datetime, timedelta, timezone
import hashlib
import os
from typing import Annotated, Literal
from uuid import UUID, uuid5

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from pydantic import Field, ValidationError
from sqlalchemy import exists, func, inspect, select, update
from sqlalchemy.orm import aliased
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
from app.services import foundry_holdout as holdout
from app.services.economic_control import require_no_containment
from app.services.specialist_triggers import enqueue_prime, outcome_scope_key
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
    body = jsonable_encoder({"scope": scope, "action_id": ref, "phase": phase, "actor": ACTORS[phase],
                             "recorded_at": datetime.now(timezone.utc).isoformat(),
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
        if not chain and phase == "mandate":
            previous = body.get("evidence", {}).get("upstream_sha256")
        if (phase != phases[index] or row.event_id != event_key(run_id, phase)
                or body.get("action_id", row.event_id) != row.event_id
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
    if mandate.get("upstream_sha256"):
        from app.routers.foundry_source_rehearsal import verify_handoff
        verify_handoff(db, run_id, mandate["upstream_sha256"])
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
    reference = review_listing(db, listing, check_new_lessons="outcome" not in chain)
    if reference != mandate["prime_decision"]:
        raise HTTPException(409, "Prime decision evidence changed")
    return chain, mandate, scope


def review_listing(db, listing, *, check_new_lessons=True):
    asset = checkout.load_artifact(db, listing.artifact_id, lock=True)
    return _bound_prime_decision(db, listing.prime_verdict_id, listing, {
        **listing.model_dump(), "product_asset": {"artifact_id": str(asset.id), "sha256": asset.sha256},
    }, check_new_lessons=check_new_lessons)


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
    if phase == "outcome" and "norns_contribution_error" in evidence:
        enqueue_prime(db, outcome_scope_key(receipt["scope"]), f"FOL-{run_id.hex}",
                      datetime.now(timezone.utc).replace(tzinfo=None), subscription="on_economic_reassessment")
    commit(db)
    return receipt


@router.post("/{run_id}/mandate", dependencies=[Depends(require_prime_control_key), Depends(require_owner_mandate_key)])
def mandate(run_id: UUID, request: Mandate, db: Session = Depends(get_db)):
    if db.scalar(select(Event.id).filter_by(event_id=f"FSO-{run_id.hex}-authority")) is not None:
        raise HTTPException(409, "Use the reviewed source-run mandate")
    return grant_mandate(run_id, request, db)


def grant_mandate(run_id, request, db, *, upstream_sha256=None):
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
    prediction = {
        "basis": "DECLARED_NO_REFUND_SCENARIO", "cohort": "DISPOSABLE_OPERATING_FIXTURE", "currency": "CAD",
        "playbook": listing.model_dump(mode="json", include={"product_id", "artifact_id", "price_cents_cad"}),
        "expected_contribution_minor": listing.price_cents_cad - request.cost_minor,
        "expected_cost_minor": request.cost_minor,
        "alternative": {"name": "FULL_REFUND", "contribution_minor": -request.cost_minor},
        "uncertainty": "REFUND_RATE_UNVERIFIED",
        "deadline_at": datetime.fromtimestamp(grant["expires_at_epoch"], timezone.utc).isoformat(),
    }
    result = add_receipt(db, run_id, "mandate", scope, {
        **request.model_dump(mode="json"), "listing": listing.model_dump(mode="json"), "grant": grant,
        "plan_sha256": plan["sha256"], "prime_decision": decision,
        "prediction": prediction,
        **({"upstream_sha256": upstream_sha256} if upstream_sha256 else {}),
    }, upstream_sha256)
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
    result = {"mimir_claim": verify_mimir_claims(db, scope, [evidence])[0],
            "support_receipt": proof["support_resolution"]["event_id"], "checkout_sha256": proof["sha256"],
            "outstanding_obligation_minor": 0, "uncommitted_cash_minor": 0, "commercial_revenue_verified": False}
    if "prediction" in mandate:
        from app.pantheon.forecasts import operating_contribution_error

        observed_at = datetime.now(timezone.utc).isoformat()
        result["prediction_observed_at"] = observed_at
        result["norns_contribution_error"] = operating_contribution_error(
            mandate["prediction"], proof["fixture_contribution_minor"], observed_at,
        )
    return result


def verify_operating_variance(db, scope, claim, *, current=True):
    from app.pantheon.forecasts import operating_contribution_error

    try:
        if set(claim) != {"basis", "run_id", "sha256"}:
            raise ValueError
        run_id = UUID(claim["run_id"])
        chain = read_run(db, run_id)
        if chain["mandate"]["scope"] != scope or chain["outcome"]["sha256"] != claim["sha256"]:
            raise ValueError
        if current and (datetime.fromisoformat(chain["outcome"]["recorded_at"]) <
                        datetime.now(timezone.utc) - timedelta(days=30)
                        or db.scalar(select(Event.id).filter_by(event_id=f"FOL-{run_id.hex}-revoked"))):
            raise HTTPException(409, "Operating lesson is revoked or stale")
        mandate = chain["mandate"]["evidence"]
        outcome = chain["outcome"]["evidence"]
        if mandate.get("upstream_sha256"):
            from app.routers.foundry_source_rehearsal import source_evidence, history, head

            source_chain = history(db, run_id)
            handoff = source_chain["handoff"]
            source = head(source_chain)
            if handoff["sha256"] != mandate["upstream_sha256"] or handoff["evidence"]["source"] != source:
                raise ValueError
            source_evidence(db, source, scope)
        proof = outcome["mimir_claim"]
        confirmed = verify_mimir_claims(db, scope, [{key: proof[key] for key in (
            "basis", "record_id", "sha256", "period_net_minor",
        )}])[0]
        prediction = mandate["prediction"]
        observed_at = outcome["prediction_observed_at"]
        variance = operating_contribution_error(prediction, confirmed["period_net_minor"], observed_at)
        if (variance != outcome["norns_contribution_error"] or confirmed != proof
                or not chain["statement"]["recorded_at"] <= observed_at <= chain["outcome"]["recorded_at"]):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise HTTPException(409, "Mimir operating variance lacks intact scoped evidence") from None
    return {**claim, "run_id": str(run_id), "prediction": prediction, "variance": variance,
            "evidence_scope": "DISPOSABLE_OPERATING_FIXTURE_ONLY"}


def current_operating_lessons(db, scope, listing):
    """Retrieve current completed runs for this exact playbook, never across scopes."""
    keys = ("product_id", "artifact_id", "price_cents_cad")
    if (not isinstance(listing, dict) or any(listing.get(key) is None for key in keys)
            or not all(isinstance(value, str) and value for value in scope.values())
            or not inspect(db.connection()).has_table(Event.__tablename__)):
        return ()
    from sqlalchemy import JSON, cast

    mandate, outcome = aliased(Event), aliased(Event)
    # PostgreSQL casts text to JSON; SQLite's JSON functions already accept text.
    body = (cast(mandate.payload_json, JSON) if db.get_bind().dialect.name == "postgresql"
            else func.json(mandate.payload_json, type_=JSON))
    playbook = body["evidence"]["prediction"]["playbook"]
    rows = db.execute(select(mandate.event_id, outcome.payload_json).join(
        outcome, outcome.event_id == func.substr(mandate.event_id, 1, 36) + "-outcome",
    ).where(
        mandate.event_type == EVENT, mandate.legacy_instance_id == scope["legacy_instance_id"],
        mandate.event_id.like("FOP-%-mandate"), outcome.event_type == EVENT,
        *(body["scope"][key].as_string() == value for key, value in scope.items()),
        playbook["product_id"].as_string() == listing["product_id"],
        playbook["artifact_id"].as_string() == listing["artifact_id"],
        playbook["price_cents_cad"].as_integer() == listing["price_cents_cad"],
        ~exists(select(Event.id).where(Event.event_id == "FOL-" + func.substr(mandate.event_id, 5, 32) + "-revoked")),
    ).order_by(outcome.id.desc()).limit(20)).all()
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    lessons = []
    for ref, content in rows:
        body = _json(content, {})
        try:
            if datetime.fromisoformat(body["recorded_at"]) < cutoff:
                continue
            proof = verify_operating_variance(db, scope, {
                "basis": "FOUNDRY_OPERATING_VARIANCE", "run_id": ref[4:36], "sha256": body["sha256"],
            })
        except (KeyError, TypeError, ValueError):
            raise HTTPException(409, "Automatic operating lesson failed integrity verification") from None
        if proof["variance"]["classification"] == "BELOW_EXPECTATION":
            lessons.append(proof["sha256"])
    return tuple(lessons)


def verify_operating_trigger(db, scope, event_id):
    try:
        run_id = UUID(event_id.removeprefix("FOL-"))
    except ValueError:
        raise HTTPException(409, "Operating learning trigger is invalid") from None
    outcome = read_run(db, run_id).get("outcome")
    if outcome is None:
        raise HTTPException(409, "Operating learning trigger has no completed outcome")
    return verify_operating_variance(db, scope, {"basis": "FOUNDRY_OPERATING_VARIANCE", "run_id": str(run_id),
                                                 "sha256": outcome["sha256"]})


@router.post("/{run_id}/learning-revocation",
             dependencies=[Depends(require_prime_control_key), Depends(require_owner_mandate_key)])
def revoke_operating_lesson(run_id: UUID, db: Session = Depends(get_db)):
    chain = read_run(db, run_id)
    if "outcome" not in chain:
        raise HTTPException(409, "Operating lesson has no completed outcome")
    ref = f"FOL-{run_id.hex}-revoked"
    if not db.scalar(select(Event.id).filter_by(event_id=ref)):
        _event(db, event_id=ref, legacy_instance_id=chain["mandate"]["scope"]["legacy_instance_id"],
               event_type="FOUNDRY_LESSON_REVOKED", message="Owner revoked operating lesson",
               payload={"outcome_sha256": chain["outcome"]["sha256"]})
        commit(db)
    return {"revoked": True, "outcome_sha256": chain["outcome"]["sha256"]}


@router.post("/{run_id}/advance", dependencies=[Depends(require_prime_control_key)])
def advance(run_id: UUID, db: Session = Depends(get_db)):
    chain, mandate, scope = active(db, run_id)
    order_id = run_ref(run_id, "order")
    if "outcome" in chain:
        claim = chain["outcome"]["evidence"]["mimir_claim"]
        verify_mimir_claims(db, scope, [{k: claim[k] for k in ("basis", "record_id", "sha256", "period_net_minor")}])
        if "prediction" in mandate:
            verify_operating_variance(db, scope, {"basis": "FOUNDRY_OPERATING_VARIANCE", "run_id": str(run_id),
                                                  "sha256": chain["outcome"]["sha256"]}, current=False)
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


def holdout_event(db, run_id, suffix, event_type):
    ref = f"FOH-{run_id.hex}-{suffix}"
    row = db.scalar(select(Event).filter_by(event_id=ref))
    if row is None:
        return None
    body = _json(row.payload_json, {})
    digest = body.pop("sha256", None) if isinstance(body, dict) else None
    if (row.event_type != event_type or not digest or body.get("scope", {}).get("legacy_instance_id") != row.legacy_instance_id
            or digest != artifact_digest(event_type, ref, body)):
        raise HTTPException(409, "Holdout journal integrity failed")
    return {**body, "sha256": digest}


def record_holdout_event(db, run_id, suffix, event_type, scope, value):
    ref = f"FOH-{run_id.hex}-{suffix}"
    body = {"scope": scope, **value}
    body["sha256"] = artifact_digest(event_type, ref, body)
    _event(db, event_id=ref, legacy_instance_id=scope["legacy_instance_id"], event_type=event_type,
           message=suffix, payload=body)
    commit(db)
    return body


@router.post("/{run_id}/economic-holdout",
             dependencies=[Depends(require_prime_control_key), Depends(require_owner_mandate_key)])
def freeze_operating_holdout(run_id: UUID, request: holdout.Plan, db: Session = Depends(get_db)):
    guard(db)
    scope = read_run(db, run_id)["mandate"]["scope"]
    lesson = verify_operating_variance(db, scope, {"basis": "FOUNDRY_OPERATING_VARIANCE", "run_id": str(run_id),
                                                   "sha256": request.training_outcome_sha256})
    existing = holdout_event(db, run_id, "plan", holdout.PLAN)
    if existing is not None:
        if existing["request"] != request.model_dump(mode="json"):
            raise HTTPException(409, "Holdout plan was already frozen")
        return existing
    plan = holdout.freeze(run_id, request, lesson)
    return record_holdout_event(db, run_id, "plan", holdout.PLAN, scope, {
        "request": request.model_dump(mode="json"), "plan": plan,
    })


@router.get("/{run_id}/economic-holdout/review-artifact", dependencies=[Depends(require_prime_control_key)])
def holdout_review_artifact(run_id: UUID, db: Session = Depends(get_db), *, result: bool = False):
    record = holdout_event(db, run_id, "result" if result else "plan", holdout.RESULT if result else holdout.PLAN)
    if record is None:
        raise HTTPException(404, "Holdout review evidence unavailable")
    return {"artifact_type": "operating_holdout", "heimdall_reference_id": str(run_id), "raw_input": record,
            "artifact_sha256": artifact_digest("operating_holdout", str(run_id), record)}


@router.post("/{run_id}/economic-holdout/{review_id}", dependencies=[Depends(require_prime_control_key)])
def observe_operating_holdout(run_id: UUID, review_id: UUID, request: holdout.Outcome, db: Session = Depends(get_db)):
    from app.loki.models import LokiIndependentReceipt, LokiReview
    from app.loki.review_service import verdict

    guard(db)
    artifact = holdout_review_artifact(run_id, db)
    record = artifact["raw_input"]
    if record["sha256"] != request.plan_sha256:
        raise HTTPException(409, "Observation does not bind the frozen holdout")
    verify_operating_variance(db, record["scope"], {"basis": "FOUNDRY_OPERATING_VARIANCE", "run_id": str(run_id),
                              "sha256": record["plan"]["training_outcome_sha256"]})
    review = db.get(LokiReview, review_id)
    if review is None or review.artifact_sha256 != artifact["artifact_sha256"] or review.artifact_type != "operating_holdout":
        raise HTTPException(409, "Independent review of the exact holdout plan is required")
    decision = verdict(db, review)
    if decision.result_severity == "critical":
        raise HTTPException(409, "Independent Loki review rejected the holdout design")
    peer = db.get(LokiIndependentReceipt, review_id)
    reviewed_at = peer.created_at.replace(tzinfo=timezone.utc) if peer.created_at.tzinfo is None else peer.created_at
    inputs = request.model_dump(mode="json")
    existing = holdout_event(db, run_id, "result", holdout.RESULT)
    if existing is not None:
        if existing["observation"] != inputs or existing["loki_result_sha256"] != decision.result_sha256:
            raise HTTPException(409, "A different holdout outcome was already recorded")
        return existing
    result = holdout.score(record["plan"], request, review_time=reviewed_at)
    return record_holdout_event(db, run_id, "result", holdout.RESULT, record["scope"], {
        **result, "plan_sha256": record["sha256"], "loki_result_sha256": decision.result_sha256,
        "review_id": str(review_id), "observation": inputs,
    })
