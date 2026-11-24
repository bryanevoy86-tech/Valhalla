"""Build reproducible internal Legacy clone and mirror rehearsals."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from statistics import median
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.completion_registry import (
    LegacyGovernancePolicy, LegacyInstancePolicyState, LegacyInstanceRegistryItem, LegacyOrchestrationEvent,
)
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyInstanceWorkItem
from app.models.media_engine import MediaContent
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.economic_control import require_no_containment
from app.services.prime_business_execution import (
    _check_legacy, _emergency_stop_active, _event, _json, require_owner_mandate_key, verified_internal_outcomes,
)


REHEARSAL_EVENT = "LEGACY_PLAYBOOK_REHEARSED"


def require_playbook_schema(db: Session = Depends(get_db)) -> None:
    schema = inspect(db.connection())
    required = (LegacyInstanceRegistryItem, LegacyInstancePolicyState, LegacyGovernancePolicy, LegacyOrchestrationEvent)
    if any(not schema.has_table(model.__tablename__) for model in required):
        raise HTTPException(status_code=503, detail="Legacy playbook schema not ready")


router = APIRouter(
    prefix="/api/prime/legacy-playbooks", tags=["legacy-playbooks"],
    dependencies=[Depends(require_prime_control_key), Depends(require_playbook_schema)],
)


class PlaybookIn(BaseModel):
    kind: Literal["BUSINESS_CLONE", "REGIONAL_MIRROR"]
    source_legacy_id: str = Field(pattern=r"^[A-Za-z0-9_-]{3,80}$")
    source_business_id: str = Field(pattern=r"^[A-Za-z0-9_-]{3,120}$")
    source_jurisdiction: str = Field(pattern=r"^[A-Z0-9-]{2,80}$")
    target_legacy_id: str = Field(pattern=r"^[A-Za-z0-9_-]{3,80}$")
    target_business_id: str = Field(pattern=r"^[A-Za-z0-9_-]{3,120}$")
    target_jurisdiction: str = Field(pattern=r"^[A-Z0-9-]{2,80}$")
    target_display_name: str = Field(min_length=3, max_length=180)
    engine_id: str = Field(pattern=r"^[A-Za-z0-9_-]{3,80}$")


def _plan_event_id(target_id: str) -> str:
    return "PLAYBOOK-" + hashlib.sha256(target_id.encode()).hexdigest()


def _recorded(db: Session, target_id: str) -> dict | None:
    event = db.query(LegacyOrchestrationEvent).filter_by(
        event_id=_plan_event_id(target_id), event_type=REHEARSAL_EVENT, legacy_instance_id=target_id,
    ).one_or_none()
    return json.loads(event.payload_json) if event else None


@router.get("/{target_id}")
def read_playbook(target_id: str, db: Session = Depends(get_db)):
    record = _recorded(db, target_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Legacy playbook not found")
    return record


@router.post("", status_code=201, dependencies=[Depends(require_owner_mandate_key)])
def rehearse_playbook(payload: PlaybookIn, db: Session = Depends(get_db)):
    if payload.source_legacy_id == payload.target_legacy_id:
        raise HTTPException(status_code=422, detail="Choose a distinct target Legacy")
    same_business = payload.source_business_id == payload.target_business_id
    if payload.kind == "REGIONAL_MIRROR" and (not same_business or payload.source_jurisdiction == payload.target_jurisdiction):
        raise HTTPException(status_code=422, detail="A regional mirror keeps the business identity and requires a distinct jurisdiction")
    if payload.kind == "BUSINESS_CLONE" and same_business:
        raise HTTPException(status_code=422, detail="A business clone needs its own business identity")

    spec = payload.model_dump()
    previous = _recorded(db, payload.target_legacy_id)
    if previous:
        if previous["specification"] != spec:
            raise HTTPException(status_code=409, detail="Target already has a different playbook")
        return previous

    source = db.query(LegacyInstanceRegistryItem).filter_by(
        legacy_instance_id=payload.source_legacy_id,
    ).with_for_update().one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Source Legacy not registered")
    _check_legacy(
        db, legacy_instance_id=payload.source_legacy_id, business_id=payload.source_business_id,
        engine_id=payload.engine_id, jurisdiction=payload.source_jurisdiction,
    )
    source_state = db.query(LegacyInstancePolicyState).filter_by(
        legacy_instance_id=payload.source_legacy_id, sync_status="SYNCED",
    ).with_for_update().all()
    if len(source_state) != 1:
        raise HTTPException(status_code=409, detail="Source needs a single synchronized governance policy")
    policy = db.query(LegacyGovernancePolicy).filter_by(
        policy_id=source_state[0].policy_id, policy_version=source_state[0].policy_version, active=True,
    ).with_for_update().one_or_none()
    if policy is None:
        raise HTTPException(status_code=409, detail="Source policy is no longer current")
    governance = {"policy_id": policy.policy_id, "policy_version": policy.policy_version}
    source_context = json.loads(source.local_knowledge_context_json)
    if source_context.get("governance") != governance:
        raise HTTPException(status_code=409, detail="Source context must match synchronized governance")

    event_id = _plan_event_id(payload.target_legacy_id)
    namespace = "legacy-rehearsals/" + event_id.removeprefix("PLAYBOOK-")
    record = {
        "playbook_version": 1, "receipt_id": event_id, "status": "REGISTRY_REHEARSED",
        "specification": spec, "source_governance": governance, "target_namespace": namespace,
        "live_traffic_routed": False, "live_sync_verified": False, "external_authority": False,
        "required_evidence": [
            "TARGET_JURISDICTION_REVIEW", "INDEPENDENT_DATA_NAMESPACE_PROOF", "TARGET_POLICY_SYNC_PROOF",
            "INTEGRATIONS_AND_AUTHORIZATION", "STAGED_RUNTIME_AND_ROLLBACK_PROOF",
        ] + (["REGIONAL_REPLICATION_AND_FAILOVER_PROOF"] if payload.kind == "REGIONAL_MIRROR"
             else ["INDEPENDENT_BUSINESS_PLAYBOOK_REVIEW"]),
    }
    db.add(LegacyInstanceRegistryItem(
        legacy_instance_id=payload.target_legacy_id, display_name=payload.target_display_name,
        parent_instance_id=payload.source_legacy_id, assigned_businesses_json=json.dumps([payload.target_business_id]),
        assigned_jurisdictions_json=json.dumps([payload.target_jurisdiction]), engines_json="[]",
        permissions_json="{}", integrations_json="{}", status="EXTERNAL_OWNER_ACTION_REQUIRED",
        synchronization_status="PENDING", isolation_state="ISOLATED", failover_state="NOT_TRIGGERED",
        audit_state="PLAYBOOK_REHEARSED",
        local_knowledge_context_json=json.dumps({
            "business_id": payload.target_business_id, "jurisdiction": payload.target_jurisdiction,
            "data_namespace": namespace, "playbook_receipt_id": event_id,
        }),
    ))
    _event(db, event_id=event_id, legacy_instance_id=payload.target_legacy_id, event_type=REHEARSAL_EVENT,
           message="Isolated target Registry row rehearsed without deployment", payload=record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        previous = _recorded(db, payload.target_legacy_id)
        if previous and previous["specification"] == spec:
            return previous
        raise HTTPException(status_code=409, detail="Target Legacy already exists") from None
    return record


# Reusable versions live next to the existing Legacy rehearsal receipts. They
# describe an internal procedure and never grant its execution.
REUSE_EVENT = "MIMIR_WORKFLOW_PLAYBOOK_VERSION"


class WorkflowVersionIn(StrictModel):
    scope: MarketScope
    name: str = Field(pattern=r"^[a-z0-9-]{3,60}$")
    version: int = Field(ge=1, le=1000)
    previous_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    outcome_ids: list[str] = Field(min_length=1, max_length=5)
    input_contract: list[str] = Field(min_length=1, max_length=20)
    acceptance_checks: list[str] = Field(min_length=1, max_length=20)
    rollback_procedure: str = Field(min_length=10, max_length=1200)
    data_class: Literal["SYNTHETIC", "INTERNAL"]
    maximum_evidence_age_days: int = Field(default=30, ge=1, le=90)


class WorkflowReuseIn(StrictModel):
    source: MarketScope
    target: MarketScope
    name: str = Field(pattern=r"^[a-z0-9-]{3,60}$")
    version: int = Field(ge=1, le=1000)
    expected_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    data_class: Literal["SYNTHETIC", "INTERNAL"]


def _workflow_reference(scope, name, version):
    return "WORKFLOW-" + artifact_digest(REUSE_EVENT, name, {"scope": scope, "version": version})


def _workflow_record(db, scope, name, version):
    key = _workflow_reference(scope, name, version)
    row = db.query(LegacyOrchestrationEvent).filter_by(event_id=key).one_or_none()
    if row is None:
        return None
    receipt = _json(row.payload_json, {})
    value = receipt.get("value") if isinstance(receipt, dict) else None
    if (row.event_type != REUSE_EVENT or row.legacy_instance_id != scope["legacy_instance_id"]
            or not isinstance(value, dict) or value.get("scope") != scope
            or receipt.get("sha256") != artifact_digest(REUSE_EVENT, key, value)):
        raise HTTPException(409, "Workflow journal failed scope or integrity verification")
    return {**value, "sha256": receipt["sha256"]}


def _source_workflow_policy(db, scope, *, lock=False):
    legacy = _check_legacy(db, **scope, lock=lock)
    policy = _json(legacy.local_knowledge_context_json, {}).get("governance")
    if not isinstance(policy, dict) or set(policy) != {"policy_id", "policy_version"}:
        raise HTTPException(409, "A current synchronized Legacy policy is required for workflow reuse")
    return policy


def _workflow_proofs(db, scope, refs, max_age_days):
    if len(set(refs)) != len(refs) or any(not re.fullmatch(r"MIMIR-[a-f0-9]{64}", ref) for ref in refs):
        raise HTTPException(422, "Distinct exact Mimir outcome IDs required")
    schema = inspect(db.connection())
    if any(not schema.has_table(model.__tablename__) for model in (LegacyInstanceWorkItem, MediaContent)):
        raise HTTPException(503, "Verified workflow outcome sources are unavailable")
    proofs = []
    now = datetime.now(timezone.utc)
    for ref in sorted(refs):
        matches = verified_internal_outcomes(db, **scope, limit=0, trigger_event_id=ref)
        try:
            if len(matches) != 1 or matches[0]["outcome_event_id"] != ref or matches[0]["sales_verified"] is not False:
                raise ValueError
            item = matches[0]
            observed = datetime.fromisoformat(item["observed_at"])
            if observed.tzinfo is None:
                observed = observed.replace(tzinfo=timezone.utc)
            if not now - timedelta(days=max_age_days) <= observed <= now:
                raise ValueError
            proof = {"outcome_event_id": ref, "artifact_sha256": item["artifact_sha256"],
                     "observed_at": item["observed_at"]}
            observation = item.get("execution_observation")
            if observation is not None:
                if (not isinstance(observation, dict)
                        or observation.get("kind") != "INTERNAL_DETERMINISTIC_DRAFT"
                        or type(observation.get("elapsed_ms")) is not int or observation["elapsed_ms"] < 0
                        or type(observation.get("provider_calls")) is not int or observation["provider_calls"] != 0
                        or type(observation.get("provider_cost_minor_cad")) is not int
                        or observation["provider_cost_minor_cad"] != 0):
                    raise ValueError
                proof["execution_observation"] = observation
            proofs.append(proof)
        except (ValueError, KeyError, TypeError):
            raise HTTPException(409, "Workflow outcome is missing, stale or outside its approved scope") from None
    return proofs


@router.post("/workflow-versions/record", status_code=201, dependencies=[Depends(require_owner_mandate_key)])
def record_workflow_version(payload: WorkflowVersionIn, db: Session = Depends(get_db)):
    scope, version = payload.scope.model_dump(), payload.version
    if any(not 1 <= len(text.strip()) <= 240 for field in (payload.input_contract, payload.acceptance_checks) for text in field):
        raise HTTPException(422, "Workflow input and acceptance entries must be bounded and meaningful")
    policy = _source_workflow_policy(db, scope, lock=True)
    prior = _workflow_record(db, scope, payload.name, version - 1) if version > 1 else None
    if (version > 1 and prior is None) or payload.previous_sha256 != (prior["sha256"] if prior else None):
        raise HTTPException(409, "Prior workflow version and digest do not match")
    outcomes = _workflow_proofs(db, scope, payload.outcome_ids, payload.maximum_evidence_age_days)
    record = {**payload.model_dump(), "outcome_ids": sorted(payload.outcome_ids),
              "source_policy": policy, "verified_internal_outcomes": outcomes, "external_authority": False,
              "execution_authorized": False, "commercial_outcome_verified": False}
    key = _workflow_reference(scope, payload.name, version)
    existing = _workflow_record(db, scope, payload.name, version)
    if existing is not None:
        if {field: existing.get(field) for field in record} != record:
            raise HTTPException(409, "Workflow version is immutable")
        return existing
    digest = artifact_digest(REUSE_EVENT, key, record)
    _event(db, event_id=key, legacy_instance_id=scope["legacy_instance_id"], event_type=REUSE_EVENT,
           message="Versioned workflow linked to exact verified internal outcomes",
           payload={"value": record, "sha256": digest})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Concurrent workflow version exists; replay the exact request") from None
    return {**record, "sha256": digest}


@router.post("/workflow-versions/assess")
def assess_workflow_reuse(payload: WorkflowReuseIn, db: Session = Depends(get_db)):
    source, target = payload.source.model_dump(), payload.target.model_dump()
    record = _workflow_record(db, source, payload.name, payload.version)
    if record is None or record["sha256"] != payload.expected_sha256:
        raise HTTPException(409, "Exact workflow version and digest required")
    reasons = []
    if source != target:
        reasons.append("CROSS_SCOPE_LOKI_AND_LOCAL_REVIEW_REQUIRED")
    if payload.data_class != record["data_class"]:
        reasons.append("DATA_CLASS_CHANGED")
    if _workflow_record(db, source, payload.name, payload.version + 1) is not None:
        reasons.append("WORKFLOW_SUPERSEDED")
    current_proofs = []
    try:
        if _source_workflow_policy(db, source) != record["source_policy"]:
            reasons.append("POLICY_CHANGED")
        proofs = _workflow_proofs(db, source, record["outcome_ids"], record["maximum_evidence_age_days"])
        if proofs != record["verified_internal_outcomes"]:
            reasons.append("OPERATING_EVIDENCE_CHANGED")
        else:
            current_proofs = proofs
        require_no_containment(db, source)
    except HTTPException as error:
        if error.status_code != 409:
            raise
        reasons.append("SOURCE_EVIDENCE_POLICY_OR_CONTAINMENT_HOLD")
    if _emergency_stop_active(db):
        reasons.append("EMERGENCY_STOP")
    baseline = [proof["execution_observation"]["elapsed_ms"]
                for proof in current_proofs if "execution_observation" in proof]
    return {"status": "REUSE_REVIEW_REQUIRED" if reasons else "DETERMINISTIC_CANDIDATE",
            "review_reasons": reasons,
            "historical_draft_baseline": {
                "sample_count": len(baseline), "median_elapsed_ms": median(baseline) if baseline else None,
                "provider_cost_minor_cad": 0 if baseline else None,
                "includes_failed_attempts": False,
            }, "playbook_sha256": record["sha256"],
            "verified_internal_outcome_count": len(record["verified_internal_outcomes"]),
            "external_authority": False, "execution_authorized": False}
