"""Normalize authorized local source exports with resumable transaction-bound jobs."""
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi import HTTPException
from pydantic import AwareDatetime, Field, model_validator
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.loki.evidence import artifact_digest
from app.models.completion_registry import SourceRegistryItem
from app.models.foundry_evidence import FoundryEvidence
from app.models.foundry_intake import FoundryIntakeJob
from app.schemas.market_intelligence import StrictModel
from app.services.foundry_discovery import EvidenceIn, SCOPE_FIELDS
from app.services.market_intelligence import authorized_source
from app.services.prime_business_execution import _check_legacy, _emergency_stop_active
from app.services.specialist_triggers import enqueue_prime, enqueue_research, outcome_scope_key


class Intake(StrictModel):
    evidence: EvidenceIn
    source_id: Annotated[str, Field(min_length=3, max_length=80)]
    external_key: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{3,80}$")]
    adapter: Literal["DEMAND_EXPORT", "PROCUREMENT_EXPORT"]
    buyer_segment: Annotated[str, Field(min_length=3, max_length=120)]
    sample_count: Annotated[int, Field(strict=True, ge=1, le=1_000_000)]
    demand_count: Annotated[int, Field(strict=True, ge=0, le=1_000_000)]
    source_signature: str | None = Field(None, pattern=r"^[0-9a-f]{128}$")
    source_signed_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def observation_bounds(self):
        if (self.demand_count > self.sample_count or self.evidence.provenance is not None
                or bool(self.source_signature) != bool(self.source_signed_at)):
            raise ValueError("Invalid observation counts or caller-supplied provenance")
        return self


def intake_ready(db):
    schema = inspect(db.connection())
    return all(schema.has_table(model.__tablename__)
               for model in (FoundryIntakeJob, SourceRegistryItem, FoundryEvidence))


def current_time():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def source_signature_message(request):
    normalized = request if isinstance(request, dict) else request.model_dump(mode="json", exclude_none=True)
    signed = {key: value for key, value in normalized.items() if key != "source_signature"}
    return artifact_digest("foundry_signed_export_v1", signed["source_id"], signed).encode("ascii")


def source_for(db, request, today, *, lock=False, verify_enrollment_time=False):
    evidence = request.evidence
    source = authorized_source(db, request.source_id, evidence.jurisdiction, evidence.evidence_class, lock=lock)
    maximum_age = min(30, max(0, (source.freshness_sla_hours or 168) // 24))
    if source.source_type.upper() != request.adapter:
        raise HTTPException(409, "Source does not permit the specified discovery adapter")
    if not today - timedelta(days=maximum_age) <= evidence.observed_on <= today <= evidence.expires_on:
        raise HTTPException(409, "Discovery observation is stale or future-dated")
    method = source.provenance_method or ""
    if evidence.evidence_class == "OPERATOR_REPORTED":
        try:
            rights = urlsplit(source.rights_statement_url or "")
        except ValueError:
            raise HTTPException(409, "External discovery source rights URL is invalid") from None
        if (source.governance_status != "approved"
                or source.permission_status not in {"public", "licensed", "authorized"}
                or source.license_status not in {"government_open_data", "open", "licensed", "consented_internal_use"}
                or rights.scheme != "https" or not rights.hostname or rights.username or rights.password
                or not method.startswith("ed25519:") or request.source_signature is None):
            raise HTTPException(409, "External discovery export requires approved source rights and a signed publisher envelope")
    if method.startswith("ed25519:"):
        if request.source_signature is None:
            raise HTTPException(409, "Registered source requires a signed export")
        try:
            public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(method.removeprefix("ed25519:")))
            public_key.verify(bytes.fromhex(request.source_signature), source_signature_message(request))
        except (ValueError, InvalidSignature):
            raise HTTPException(409, "Discovery export signature does not match the registered source") from None
        if verify_enrollment_time:
            received = datetime.now(timezone.utc)
            if not received - timedelta(minutes=15) <= request.source_signed_at <= received + timedelta(seconds=30):
                raise HTTPException(409, "Discovery export signature timestamp is outside the intake window")
    elif request.source_signature:
        raise HTTPException(409, "No signature key is enrolled for this source")
    return source


def key_for(request):
    scope = request.evidence.model_dump(include=SCOPE_FIELDS)
    return artifact_digest("foundry_observation", outcome_scope_key(scope), {
        "source_id": request.source_id, "external_key": request.external_key.casefold(),
        "observed_on": request.evidence.observed_on.isoformat(),
    })


def job_view(job):
    return {"job_id": job.id, "status": job.status, "attempts": job.attempts,
            "error_code": job.error_code, "commercial_validation": False}


def materialize(db, job, now):
    if job.digest != artifact_digest("foundry_intake", str(job.id), job.payload):
        raise HTTPException(409, "Discovery job evidence failed integrity")
    request = Intake.model_validate(job.payload)
    if job.id != request.evidence.evidence_id or key_for(request) != job.observation_key:
        raise HTTPException(409, "Discovery job metadata was changed")
    evidence = request.evidence
    scope = evidence.model_dump(include=SCOPE_FIELDS)
    _check_legacy(db, **scope)
    source_for(db, request, now.date(), lock=True)
    source_ref = f"{request.source_id}:{request.external_key.casefold()}"
    payload = evidence.model_dump(mode="json", exclude_none=True)
    payload["source_ref"] = source_ref
    payload["provenance"] = {
        "source_id": request.source_id, "adapter": request.adapter, "citation": evidence.source_ref,
        "external_key": request.external_key.casefold(), "job_sha256": job.digest,
        "sample_count": request.sample_count, "demand_count": request.demand_count,
        "buyer_segment": request.buyer_segment,
    }
    row = FoundryEvidence(id=job.id, scope_key=outcome_scope_key(scope), source_ref=source_ref,
                          observed_on=evidence.observed_on, expires_on=evidence.expires_on,
                          payload=payload, digest=artifact_digest("foundry_evidence", str(job.id), payload))
    db.add(row)
    from app.services.foundry_discovery import DISCOVERY_ROLES

    enqueue_research(db, row.scope_key, f"DISCOVERY-{job.id}", now, roles=DISCOVERY_ROLES)
    if db.scalar(select(FoundryEvidence.id).where(
        FoundryEvidence.scope_key == row.scope_key, FoundryEvidence.source_ref == source_ref,
        FoundryEvidence.observed_on < row.observed_on,
    ).limit(1)) is not None:
        enqueue_prime(db, row.scope_key, f"DISCOVERY-{job.id}", now, subscription="on_economic_reassessment")
    db.flush()


def run_intake(db, *, now=None, job_id=None, durable=True):
    """Claim one row atomically, leaving it available after process death before commit."""
    now = now or current_time()
    if not intake_ready(db):
        return {"status": "unavailable", "error_code": "SCHEMA_UNAVAILABLE"}
    if _emergency_stop_active(db):
        return {"status": "paused", "error_code": "EMERGENCY_STOP"}
    job = db.scalar(select(FoundryIntakeJob).where(
        FoundryIntakeJob.status == "QUEUED", FoundryIntakeJob.next_attempt_at <= now,
        *((FoundryIntakeJob.id == job_id,) if job_id is not None else ()),
    ).order_by(FoundryIntakeJob.next_attempt_at, FoundryIntakeJob.id).limit(1).with_for_update(skip_locked=True))
    if job is None:
        return {"status": "idle"}
    job.attempts += 1
    try:
        with db.begin_nested():
            materialize(db, job, now)
    except (HTTPException, IntegrityError, ValueError):
        job.status = "REJECTED"
        job.error_code = "SOURCE_OR_SCOPE_REJECTED"
    except OperationalError:
        job.status = "FAILED" if job.attempts >= 3 else "QUEUED"
        job.next_attempt_at = now + timedelta(minutes=2 ** job.attempts)
        job.error_code = "ADAPTER_RETRY_EXHAUSTED" if job.status == "FAILED" else "ADAPTER_RETRY_PENDING"
    else:
        job.status, job.error_code = "COMPLETED", None
    db.commit() if durable else db.flush()
    return job_view(job)


def verify_intake_trigger(db, event, scope, today):
    try:
        row = db.get(FoundryEvidence, UUID(event.removeprefix("DISCOVERY-")))
        if row is None:
            return False
        from app.services.foundry_discovery import checked_evidence

        return checked_evidence(row, scope, today, db=db).provenance is not None
    except (HTTPException, ValueError):
        return False


def source_revision(db, event, scope, today):
    """Identify which source-bound decisions require review; do not rewrite them."""
    from app.models.god_verdicts import GodVerdict
    from app.services.foundry_discovery import SCOPE_FIELDS, checked_evidence

    if not verify_intake_trigger(db, event, scope, today):
        raise HTTPException(409, "Source revision failed revalidation")
    current = db.get(FoundryEvidence, UUID(event.removeprefix("DISCOVERY-")))
    checked_evidence(current, scope, today, db=db)
    prior_rows = db.scalars(select(FoundryEvidence).where(
        FoundryEvidence.scope_key == current.scope_key, FoundryEvidence.source_ref == current.source_ref,
        FoundryEvidence.observed_on < current.observed_on,
    ).order_by(FoundryEvidence.observed_on.desc(), FoundryEvidence.id).limit(26)).all()
    prior = {}
    fields = ("unit_price", "variable_cost_per_unit", "acquisition_cost_per_unit",
              "monthly_units", "monthly_fixed_cost", "startup_capital", "test_cost", "acquisition", "provenance")
    for row in prior_rows[:25]:
        if (not isinstance(row.payload, dict) or any(row.payload.get(key) != scope[key] for key in SCOPE_FIELDS)
                or row.digest != artifact_digest("foundry_evidence", str(row.id), row.payload)):
            raise HTTPException(409, "Previous source observation failed integrity")
        prior[str(row.id)] = {"sha256": row.digest, "changed_fields": [
            key for key in fields if row.payload.get(key) != current.payload.get(key)
        ]}
    affected = []
    if prior and inspect(db.connection()).has_table(GodVerdict.__tablename__):
        decisions = db.scalars(select(GodVerdict).where(
            GodVerdict.metadata_json["foundry_evidence_id"].as_string().in_(prior),
        ).order_by(GodVerdict.created_at.desc(), GodVerdict.id).limit(26)).all()
        affected = [{"verdict_id": str(row.id), "opportunity_id": row.metadata_json["opportunity_id"],
                     "previous_evidence_id": row.metadata_json["foundry_evidence_id"]}
                    for row in decisions[:25] if row.metadata_json.get("foundry_evidence_sha256")
                    == prior[row.metadata_json["foundry_evidence_id"]]["sha256"]]
    else:
        decisions = []
    return {"new_evidence_id": str(current.id), "new_sha256": current.digest, "superseded": prior,
            "affected_decisions": affected, "truncated": len(prior_rows) > 25 or len(decisions) > 25}
