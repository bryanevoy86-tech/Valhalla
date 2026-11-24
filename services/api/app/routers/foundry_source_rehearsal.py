"""Connect signed Foundry intake to one disposable, governed operating run."""
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.loki.models import LokiIndependentReceipt, LokiReconsideration, LokiReview, LokiReviewStatus
from app.loki.review_service import record_reconsideration, reviewer_identity, verdict
from app.loki.schemas import LokiReviewCreate, OwnerReconsiderationIn
from app.loki.specialist_review import enqueue_report, require_reviewed_reports
from app.models.completion_registry import LegacyOrchestrationEvent as Event
from app.models.foundry_evidence import FoundryEvidence
from app.models.foundry_intake import FoundryIntakeJob
from app.models.specialist_assignment import SpecialistAssignment
from app.pantheon.monitor import run_assignment, utc_now, verified_report
from app.routers import foundry_checkout as checkout
from app.routers import foundry_operating_rehearsal as operating
from app.routers.auth_weweb import private_owner_response, require_owner_session
from app.routers.completion_registry import (
    UniversalOpportunityBatchIn, UniversalOpportunityIn, evaluate_opportunity_batch, universal_review_artifact,
)
from app.routers.foundry_discovery import prepare_candidate, queue_signed_intake
from app.routers.loki import queue_review
from app.routers.prime_business_factory import ListingDraftRequest
from app.routers.research_participant import profile
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.economic_control import require_no_containment
from app.services.foundry_discovery import DISCOVERY_ROLES, SCOPE_FIELDS, checked_evidence, require_current_candidate
from app.services.foundry_intake import Intake, intake_ready, run_intake
from app.services.prime_business_execution import _check_legacy, _event, _json, _listing_asset, require_owner_mandate_key

router = APIRouter(prefix="/api/foundry/source-rehearsal", tags=["foundry-source-rehearsal"])
PRIME = [Depends(require_prime_control_key)]
OWNER = [*PRIME, Depends(require_owner_mandate_key)]
EVENT = "FOUNDRY_SOURCE_REHEARSAL"
ASSUMPTIONS = {
    "evidence_confidence", "strategic_value", "downside_exposure", "blast_radius",
    "maximum_capital_exposure", "required_reserve_to_survive_failure", "available_safe_capital",
    "point_of_no_return", "exit_options",
}
LENS_ASSUMPTIONS = {
    "niche_demand", "addressable_niche", "pricing_power", "retention", "defensibility",
    "global_reach", "churn_risk", "technical_build_effort", "hosting_api_cost", "support_burden",
}


class Authority(operating.Mandate):
    source_id: Annotated[str, Field(min_length=3, max_length=80)]
    external_key: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{3,80}$")]
    assignment_ids: Annotated[list[UUID], Field(min_length=2, max_length=5)]
    scenario: UniversalOpportunityIn
    experiment_budget_minor: Annotated[int, Field(strict=True, ge=1, le=100_000)]


class AcceptSelection(StrictModel):
    decision_sha256: operating.Sha


def event_id(run_id, name):
    return f"FSO-{run_id.hex}-{name}"


def history(db, run_id):
    rows = db.scalars(select(Event).where(Event.event_id.startswith(f"FSO-{run_id.hex}-")).order_by(Event.id)).all()
    if not rows:
        raise HTTPException(404, "Source rehearsal unavailable")
    chain = {}
    previous = None
    for row in rows:
        body = _json(row.payload_json, {})
        if not isinstance(body, dict):
            raise HTTPException(409, "Malformed source-run receipt")
        digest = body.pop("sha256", None)
        key = row.event_id.removeprefix(f"FSO-{run_id.hex}-")
        if (row.event_type != EVENT or body.get("action_id") != row.event_id or body.get("previous_sha256") != previous
                or body.get("external_effects") != 0
                or digest != artifact_digest("foundry_source_rehearsal", row.event_id, body)
                or (chain and body["scope"] != chain["authority"]["scope"])
                or row.legacy_instance_id != body.get("scope", {}).get("legacy_instance_id")
                or (not chain and key != "authority")):
            raise HTTPException(409, "Source-run receipt integrity failed")
        chain[key] = {**body, "sha256": digest}
        previous = digest
    return chain


def add(db, run_id, chain, name, actor, scope, evidence):
    ref = event_id(run_id, name)
    body = jsonable_encoder({
        "action_id": ref, "actor": actor, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope, "evidence": evidence, "previous_sha256": next(reversed(chain.values()))["sha256"] if chain else None,
        "external_effects": 0,
    })
    body["sha256"] = artifact_digest("foundry_source_rehearsal", ref, body)
    _event(db, event_id=ref, legacy_instance_id=scope["legacy_instance_id"], event_type=EVENT, message=name, payload=body)
    operating.commit(db)
    return body


def current(db, run_id):
    operating.guard(db)
    if not intake_ready(db):
        raise HTTPException(503, "Discovery intake not migrated")
    db.execute(update(Event).where(Event.event_id == event_id(run_id, "authority")).values(message=Event.message))
    chain = history(db, run_id)
    policy = chain["authority"]["evidence"]
    scope = chain["authority"]["scope"]
    if policy["expires_at"] <= datetime.now(timezone.utc).timestamp():
        raise HTTPException(409, "Source authority expired")
    _check_legacy(db, **scope)
    require_no_containment(db, scope)
    return chain, policy, scope


def head(chain):
    return next((r["evidence"] for key, r in reversed(chain.items()) if key.startswith("source-")), None)


def stage(source, phase):
    return f"{phase}-{UUID(source['job_id']).hex}"


def assignments(db, ids, scope):
    rows = [db.get(SpecialistAssignment, UUID(str(assignment_id))) for assignment_id in ids]
    if (any(row is None or row.scope != scope or row.state != "active" or row.expires_at <= utc_now()
            or row.role not in DISCOVERY_ROLES for row in rows)
            or len({row.role for row in rows}) != len(ids) or not {"ODIN", "NJORD"} <= {row.role for row in rows}):
        raise HTTPException(409, "Active distinct ODIN and NJORD assignments and exact scope are required")
    return rows


@router.post("/{run_id}/authority", dependencies=OWNER)
def authorize(run_id: UUID, request: Authority, db: Session = Depends(get_db)):
    operating.guard(db)
    listing = request.listing
    if not listing.artifact_id or listing.prime_verdict_id or listing.mandate_id:
        raise HTTPException(422, "Provide a private offer without a preselected verdict")
    scope = {name: getattr(listing, name) for name in SCOPE_FIELDS}
    _check_legacy(db, **scope, lock=True)
    require_no_containment(db, scope)
    profile(db, request.buyer_id)
    assignments(db, request.assignment_ids, scope)
    _listing_asset(db, listing.artifact_id, listing, listing.product_id)
    if (db.scalar(select(Event.id).filter_by(event_id=event_id(run_id, "authority"))) is not None
            or db.scalar(select(Event.id).filter_by(event_id=operating.event_key(run_id, "mandate"))) is not None):
        raise HTTPException(409, "Run identity already used")
    config = request.model_dump(mode="json", exclude={"scenario"})
    config["scenario"] = request.scenario.model_dump(mode="json", include=ASSUMPTIONS)
    config["scenario"]["specialist_inputs"] = {
        k: v for k, v in request.scenario.specialist_inputs.items()
        if k in LENS_ASSUMPTIONS and type(v) in {int, float} and 0 <= v <= 1
    }
    config["expires_at"] = datetime.now(timezone.utc).timestamp() + request.ttl_seconds
    return add(db, run_id, {}, "authority", "OWNER_INITIAL_AUTHORITY", scope, config)


@router.post("/{run_id}/source")
def incoming(run_id: UUID, payload: Intake, db: Session = Depends(get_db)):
    chain, policy, scope = current(db, run_id)
    evidence = payload.evidence
    if (payload.source_id != policy["source_id"] or payload.external_key.casefold() != policy["external_key"].casefold()
            or not payload.source_signature or not payload.source_signed_at
            or evidence.model_dump(include=SCOPE_FIELDS) != scope or evidence.kind != "DIGITAL_PRODUCT"
            or evidence.unit_price != policy["listing"]["price_cents_cad"]
            or evidence.variable_cost_per_unit != policy["cost_minor"]):
        raise HTTPException(409, "Incoming evidence outside source authority")
    name = f"source-{evidence.evidence_id.hex}"
    old = head(chain)
    if ("handoff" in chain and name not in chain
            or (old and name not in chain and evidence.observed_on.isoformat() <= old["observed_on"])):
        raise HTTPException(409, "Refresh requires a newer observation and an unmandated run")
    if name not in chain and db.get(FoundryIntakeJob, evidence.evidence_id) is not None:
        raise HTTPException(409, "Source job already belongs to another intake")
    job = queue_signed_intake(payload, db, durable=False)
    row = db.get(FoundryIntakeJob, job["job_id"])
    if name in chain:
        if chain[name]["evidence"]["job_sha256"] != row.digest:
            raise HTTPException(409, "Source replay differs")
        return chain[name]
    return add(db, run_id, chain, name, "SIGNED_SOURCE_PUBLISHER", scope, {
        "job_id": row.id, "job_sha256": row.digest, "source_id": payload.source_id,
        "external_key": payload.external_key, "signed_at": payload.source_signed_at,
        "observed_on": evidence.observed_on,
    })


def source_evidence(db, source, scope):
    row = db.get(FoundryEvidence, UUID(source["job_id"]))
    if row is None:
        raise HTTPException(409, "Source evidence unavailable")
    evidence = checked_evidence(row, scope, utc_now().date(), db=db)
    if not evidence.provenance or evidence.provenance.job_sha256 != source["job_sha256"]:
        raise HTTPException(409, "Source provenance differs from signed intake")
    return row


def review_brief(db, reviews):
    result = []
    for ref in reviews:
        review = db.get(LokiReview, UUID(ref["id"]))
        if (review is None or review.artifact_sha256 != ref["artifact_sha256"]
                or review.artifact_type != ref["kind"]):
            raise HTTPException(409, "Queued Loki evidence changed")
        if review.status != LokiReviewStatus.COMPLETED:
            result.append({**ref, "status": "WAITING_FOR_INDEPENDENT_LOKI"})
            continue
        decision = verdict(db, review)
        receipt = db.get(LokiIndependentReceipt, review.id)
        disposition = db.get(LokiReconsideration, review.id)
        result.append({**ref, "status": "REVIEWED", "reviewer_id": receipt.reviewer_id,
                       "reviewed_at": receipt.created_at.isoformat(),
                       "headline": decision.headline, "result_sha256": decision.result_sha256,
                       "ok_to_proceed": decision.ok_to_proceed, "severity": decision.result_severity,
                       "disposition": decision.reconsideration_status,
                       "disposition_sha256": decision.reconsideration_sha256,
                       "owner_reason": disposition.reason if disposition else None,
                       "findings": [{"id": str(x.id), "category": x.category, "severity": x.severity,
                                     "message": x.message, "tags": x.tags} for x in review.findings]})
    return result


def check_review_actors(chain, brief):
    for row in brief:
        if row.get("disposition_sha256"):
            actor = chain.get(f"owner-{UUID(row['id']).hex}")
            if not actor or actor["evidence"]["disposition_sha256"] != row["disposition_sha256"]:
                raise HTTPException(409, "Disposition must be recorded in this source run")


def queue_assessments(db, policy, scope, source, report_rows):
    reviewer_identity()
    principal = next(r for r in report_rows if r["evidence"]["role"] == "ODIN")
    grounded = prepare_candidate(principal["evidence"]["report_id"], UUID(source["job_id"]), db)["proposal"]
    listing = ListingDraftRequest.model_validate(policy["listing"])
    asset = _listing_asset(db, listing.artifact_id, listing, listing.product_id)
    proposed = listing.model_dump(mode="json", include={"artifact_id", "product_id", "industry", "title",
                                                        "description", "price_cents_cad"})
    proposed["artifact_sha256"] = asset["sha256"]
    inputs = {**policy["scenario"]["specialist_inputs"], **grounded["specialist_inputs"],
              "pantheon_report_ids": [r["evidence"]["report_id"] for r in report_rows],
              "proposed_internal_listing": proposed}
    proposal = UniversalOpportunityIn.model_validate({
        **policy["scenario"], **grounded, "specialist_inputs": inputs, "persist_decision": True,
    })
    request = universal_review_artifact(proposal)
    if request["raw_input"]["simulation_fixture"] is True:
        raise HTTPException(409, "Shadow-only evidence cannot receive operating authority")
    reviews = [enqueue_report(db, r["evidence"]["report_id"], durable=False) for r in report_rows]
    reviews.append(queue_review(LokiReviewCreate(**request, input_source="disposable-source-worker"), db, durable=False))
    return {"reviews": [{"id": str(r.id), "kind": r.artifact_type, "artifact_sha256": r.artifact_sha256}
                        for r in reviews], "proposal": proposal.model_dump(mode="json"), "scope": scope}


def ready_for_decision(db, chain, source, scope, bundle):
    require_current_candidate(db, bundle["proposal"], scope, utc_now().date())
    source_evidence(db, source, scope)
    brief = review_brief(db, bundle["reviews"])
    check_review_actors(chain, brief)
    return brief


def response(receipt):
    return {"status": "advanced", "phase": receipt["action_id"].split("-", 2)[-1],
            "receipt_sha256": receipt["sha256"]}


@router.post("/{run_id}/advance", dependencies=PRIME)
def advance(run_id: UUID, db: Session = Depends(get_db)):
    # The downstream worker owns the loop after the checked handoff.
    if db.scalar(select(Event.id).filter_by(event_id=operating.event_key(run_id, "mandate"))) is not None:
        return {"status": "handoff"}
    chain, policy, scope = current(db, run_id)
    source = head(chain)
    if source is None:
        return {"status": "waiting", "reason": "SIGNED_SOURCE"}
    job_id = UUID(source["job_id"])
    name = stage(source, "intake")
    if name not in chain:
        job = db.get(FoundryIntakeJob, job_id)
        if job is None:
            raise HTTPException(409, "Authorized source job disappeared")
        state = {"status": job.status, "attempts": job.attempts}
        if job.status == "QUEUED":
            state = run_intake(db, job_id=job_id, durable=False)
        if state["status"] != "COMPLETED":
            # Keep bounded existing intake retry/rejection state without inventing a receipt.
            operating.commit(db)
            return {"status": "waiting", "reason": state["status"]}
        row = source_evidence(db, source, scope)
        return response(add(db, run_id, chain, name, "FOUNDRY_INTAKE_WORKER", scope, {
            **source, "evidence_sha256": row.digest, "attempts": state["attempts"],
        }))
    row = source_evidence(db, source, scope)
    report_rows = []
    for assignment in assignments(db, policy["assignment_ids"], scope):
        name = stage(source, f"r{assignment.role.lower()}")
        if name not in chain:
            state = run_assignment(db, assignment.role, assignment_id=assignment.id,
                                   exact_trigger=f"DISCOVERY-{job_id}", durable=False)
            if state["status"] not in {"observed", "replayed"}:
                raise HTTPException(409, "Exact specialist evidence unavailable")
            report = verified_report(db, state["report_event_id"])
            if not any(item["evidence_id"] == str(row.id) and item["sha256"] == row.digest
                       for item in report["observations"].get("foundry_signals", [])):
                raise HTTPException(409, "Specialist omitted exact evidence")
            return response(add(db, run_id, chain, name, "PANTHEON_WORKER", scope, {
                "role": assignment.role, "assignment_id": assignment.id, "report_id": report["report_event_id"],
                "report_sha256": report["report_sha256"], "source_sha256": row.digest,
            }))
        report_rows.append(chain[name])
    name = stage(source, "review")
    if name not in chain:
        bundle = queue_assessments(db, policy, scope, source, report_rows)
        return response(add(db, run_id, chain, name, "PRIME_WORKER", scope, bundle))
    bundle = chain[name]["evidence"]
    brief = ready_for_decision(db, chain, source, scope, bundle)
    completed = all(item["status"] == "REVIEWED" for item in brief)
    review_snapshot = stage(source, "loki")
    if completed and review_snapshot not in chain:
        return response(add(db, run_id, chain, review_snapshot, "PRIME_RECORDS_INDEPENDENT_LOKI", scope, {
            "independent_reviews": brief,
            "next_action": "OWNER_MATERIAL_REVIEW" if not all(x["ok_to_proceed"] for x in brief) else "PROCEED_TO_EVALUATION",
        }))
    if not all(row.get("ok_to_proceed") for row in brief):
        reason = ("INDEPENDENT_LOKI" if any(row["status"] != "REVIEWED" for row in brief)
                  else "OWNER_MATERIAL_REVIEW")
        return {"status": "waiting", "reason": reason, "briefing": brief}
    name = stage(source, "decision")
    if name in chain:
        return {"status": "waiting", "reason": chain[name]["evidence"]["next_action"], "decision_sha256": chain[name]["sha256"]}
    require_reviewed_reports(db, bundle["proposal"]["specialist_inputs"]["pantheon_report_ids"], scope)
    opportunity = next(row for row in brief if row["kind"] == "universal_opportunity")
    evaluated = evaluate_opportunity_batch(UniversalOpportunityBatchIn(opportunities=[
        UniversalOpportunityIn.model_validate({**bundle["proposal"], "independent_loki_review_id": opportunity["id"]}),
    ], shadow_mode=False), db, durable=False)["evaluations"][0]
    listing = ListingDraftRequest.model_validate({**policy["listing"],
        "prime_verdict_id": evaluated["persistence"]["god_verdict_id"]})
    permitted = False
    try:
        operating.review_listing(db, listing)
        permitted = True
    except HTTPException as exc:
        if exc.status_code != 409:
            raise
    next_action = "FINAL_OWNER_MANDATE" if permitted else "HOLD_NO_ELIGIBLE_INTERNAL_DRAFT"
    return response(add(db, run_id, chain, name, "PRIME_WORKER", scope, {
        "listing": listing.model_dump(mode="json"), "source_sha256": row.digest,
        "independent_reviews": brief, "evaluation": evaluated, "next_action": next_action,
    }))


@router.post("/{run_id}/reviews/{review_id}/disposition", dependencies=OWNER)
def reconsider(run_id: UUID, review_id: UUID, request: OwnerReconsiderationIn, db: Session = Depends(get_db)):
    chain, _, scope = current(db, run_id)
    source = head(chain)
    bundle = chain.get(stage(source, "review")) if source else None
    if not bundle or stage(source, "loki") not in chain or str(review_id) not in {r["id"] for r in bundle["evidence"]["reviews"]}:
        raise HTTPException(409, "Only a current source-run review can be disposed")
    source_evidence(db, source, scope)
    result = record_reconsideration(db, review_id, request, durable=False)
    return add(db, run_id, chain, f"owner-{review_id.hex}", "OWNER_MATERIAL_DISPOSITION", scope, {
        "review_id": review_id, "artifact_sha256": result.artifact_sha256, "disposition": result.disposition,
        "reason": result.reason, "disposition_sha256": result.decision_sha256,
        "finding_ids": result.material_finding_ids,
    })


@router.post("/{run_id}/mandate", dependencies=OWNER)
def authorize_operation(run_id: UUID, request: AcceptSelection, db: Session = Depends(get_db)):
    chain, policy, scope = current(db, run_id)
    source = head(chain)
    decision = chain.get(stage(source, "decision")) if source else None
    if (not decision or "handoff" in chain or decision["sha256"] != request.decision_sha256
            or decision["evidence"]["next_action"] != "FINAL_OWNER_MANDATE"):
        raise HTTPException(409, "An eligible current decision is required")
    bundle = chain[stage(source, "review")]["evidence"]
    if ready_for_decision(db, chain, source, scope, bundle) != decision["evidence"]["independent_reviews"]:
        raise HTTPException(409, "Decision review changed")
    plan = checkout._record_acquisition_plan(policy["campaign_id"], checkout.AcquisitionPlanIn(
        scope=MarketScope.model_validate(scope), channel="DIRECT_OPT_IN", demand_evidence_id=UUID(source["job_id"]),
        experiment_budget_minor=policy["experiment_budget_minor"], stop_after_visits=1,
    ), db, durable=False)
    request = operating.Mandate.model_validate({
        **{key: policy[key] for key in ("campaign_id", "buyer_id", "terms_sha256", "cost_minor", "ttl_seconds")},
        "listing": decision["evidence"]["listing"],
    })
    # This immutable handoff is part of the final mandate transaction.
    ref = event_id(run_id, "handoff")
    body = {"action_id": ref, "actor": "OWNER_FINAL_MANDATE", "recorded_at": datetime.now(timezone.utc).isoformat(),
            "scope": scope, "evidence": {"decision_sha256": decision["sha256"], "plan_sha256": plan["sha256"],
                                        "source": source},
            "previous_sha256": next(reversed(chain.values()))["sha256"], "external_effects": 0}
    body["sha256"] = artifact_digest("foundry_source_rehearsal", ref, body)
    _event(db, event_id=ref, legacy_instance_id=scope["legacy_instance_id"], event_type=EVENT,
           message="Owner approved exact source-run handoff", payload=body)
    return operating.grant_mandate(run_id, request, db, upstream_sha256=body["sha256"])


def verify_handoff(db, run_id, digest):
    chain = history(db, run_id)
    handoff = chain.get("handoff")
    if not handoff or handoff["sha256"] != digest or handoff["evidence"]["source"] != head(chain):
        raise HTTPException(409, "Operating handoff changed")
    source = head(chain)
    source_evidence(db, source, handoff["scope"])
    decision = chain.get(stage(source, "decision"))
    if not decision or decision["sha256"] != handoff["evidence"]["decision_sha256"]:
        raise HTTPException(409, "Operating decision no longer matches its handoff")


@router.get("/{run_id}", dependencies=PRIME)
def receipts(run_id: UUID, db: Session = Depends(get_db)):
    if not operating.enabled():
        raise HTTPException(503, "Source rehearsal disabled")
    chain = history(db, run_id)
    phases = []
    if "handoff" in chain:
        phases = list(operating.read_run(db, run_id).values())
        if phases[0]["previous_sha256"] != chain["handoff"]["sha256"]:
            raise HTTPException(409, "Operating receipt has a broken handoff")
    source = head(chain)
    queued = chain.get(stage(source, "review")) if source else None
    return {"source_receipts": list(chain.values()), "operating_receipts": phases,
            "review_briefing": review_brief(db, queued["evidence"]["reviews"]) if queued else [],
            "commercial_activation_authorized": False}


@router.get("/{run_id}/owner-briefing", dependencies=[Depends(require_owner_session)])
def owner_briefing(run_id: UUID, db: Session = Depends(get_db)):
    return private_owner_response(receipts(run_id, db))
