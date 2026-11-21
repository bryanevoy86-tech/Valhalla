"""Build reproducible internal Legacy clone and mirror rehearsals."""
import hashlib
import json
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
from app.services.prime_business_execution import _check_legacy, _event, require_owner_mandate_key


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
