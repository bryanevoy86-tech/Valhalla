"""Lease exact approved review bundles and receive isolated test evidence."""
from datetime import datetime, timedelta, timezone
import hmac
import os
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import inspect, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.core.settings import settings
from app.models.builder import BuilderEvent, BuilderTask
from app.models.builder_assignment import BuilderAssignment
from app.routers.builder import MAX_BATCH_BYTES, _canonical, _prepare_files, _read_base, _review_bundle, _sha
from app.schemas.builder import FileSpec
from app.services.prime_business_execution import _emergency_stop_active, require_owner_mandate_key


MAX_LEASE_CLAIMS = 3


def require_schema(db: Session = Depends(get_db)):
    schema = inspect(db.connection())
    if (any(not schema.has_table(model.__tablename__) for model in (BuilderTask, BuilderAssignment))
            or not any(column["name"] == "claim_count" for column in schema.get_columns(BuilderAssignment.__tablename__))):
        raise HTTPException(503, "Builder assignment schema not ready")


router = APIRouter(prefix="/builder/assignments", tags=["builder-assignments"], dependencies=[Depends(require_schema)])


def require_runner(provided: str | None = Header(None, alias="X-Builder-Runner-Key")):
    key = os.getenv("VALHALLA_BUILDER_RUNNER_KEY", "")
    if not key or key in {
        settings.BUILDER_KEY, settings.SESSION_TOKEN_DEV, settings.jwt_secret, os.getenv("VALHALLA_PRIME_CONTROL_KEY"),
        os.getenv("VALHALLA_OWNER_MANDATE_KEY"), os.getenv("VALHALLA_FACTORY_KEY"), os.getenv("VALHALLA_LOKI_REVIEWER_KEY"),
    }:
        raise HTTPException(503, "Independent Builder runner configuration unavailable")
    if not provided or not hmac.compare_digest(provided.encode(), key.encode()):
        raise HTTPException(401, "Builder runner authentication required")


class AssignmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assignment_id: UUID
    task_id: int = Field(gt=0)
    base_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    image_id: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")


class CandidateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assignment_id: UUID
    base_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    image_id: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    title: str = Field(min_length=3, max_length=140)
    path: str = Field(min_length=1, max_length=200)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    before: str = Field(min_length=1, max_length=8192)
    after: str = Field(max_length=8192)


class TestReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lease_id: UUID
    status: Literal["suite_exited_zero", "suite_exited_nonzero", "sandbox_unavailable", "sandbox_timeout"]
    exit_code: int | None
    suite: Literal["services/api/tests"]
    base_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    image_id: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    bundle_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_modified: Literal[False]
    committed: Literal[False]
    deployed: Literal[False]
    release_authorized: Literal[False]


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def view(row):
    return {"assignment_id": row.id, "task_id": row.task_id, "status": row.status, "receipt": row.receipt,
            "claim_count": row.claim_count, "base_commit": row.base_commit, "image_id": row.image_id, "bundle_sha256": row.bundle_sha256,
            "release_authorized": False}


@router.post("", status_code=201, dependencies=[Depends(require_prime_control_key), Depends(require_owner_mandate_key)])
def assign(payload: AssignmentIn, db: Session = Depends(get_db)):
    existing = db.get(BuilderAssignment, payload.assignment_id)
    if existing:
        if (existing.task_id, existing.base_commit, existing.image_id) != (payload.task_id, payload.base_commit, payload.image_id):
            raise HTTPException(409, "Assignment ID already used")
        return view(existing)
    task = db.get(BuilderTask, payload.task_id, with_for_update=True)
    if task is None or task.status != "review_ready":
        raise HTTPException(409, "Prepare the snapshot-bound candidate before queueing")
    bundle, _ = _review_bundle(task)
    row = BuilderAssignment(
        id=payload.assignment_id, task_id=payload.task_id, base_commit=payload.base_commit,
        image_id=payload.image_id, bundle_sha256=bundle["sha256"], status="queued", created_at=now(),
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Assignment ID already used") from None
    return view(row)


@router.post("/prepare", status_code=201, dependencies=[Depends(require_prime_control_key), Depends(require_owner_mandate_key)])
def prepare(payload: CandidateIn, db: Session = Depends(get_db)):
    """Generate one scoped source candidate and queue the existing runner atomically."""
    if _emergency_stop_active(db):
        raise HTTPException(503, "Builder assignment preparation paused")
    request_hash = _sha(_canonical(payload.model_dump(mode="json")))
    existing = db.get(BuilderAssignment, payload.assignment_id)
    if existing:
        prior_task = db.get(BuilderTask, existing.task_id)
        if prior_task is None or prior_task.plan != f"literal-replacement:{request_hash}":
            raise HTTPException(409, "Assignment ID already used")
        return view(existing)
    old, source_hash = _read_base(payload.path)
    match = old.find(payload.before)
    if source_hash != payload.source_sha256 or match == -1 or old.find(payload.before, match + 1) != -1:
        raise HTTPException(409, "Expected source hash and a single matching edit are required")
    records, _ = _prepare_files([
        FileSpec(path=payload.path, mode="replace", content=old.replace(payload.before, payload.after, 1)),
    ])
    if records[0]["base_sha256"] != source_hash:
        raise HTTPException(409, "Source changed during preparation")
    task = BuilderTask(title=payload.title, scope=records[0]["path"], status="review_ready",
                       plan=f"literal-replacement:{request_hash}", diff_summary="One snapshot-verified prepared file")
    db.add(task)
    try:
        db.flush()
        bundle = {"version": 2, "task_id": task.id, "files": records}
        encoded = _canonical(bundle)
        if len(encoded) > 2 * MAX_BATCH_BYTES:
            raise HTTPException(413, "Encoded Builder bundle exceeds limit")
        digest = _sha(encoded)
        task.payload_json = _canonical({"bundle": bundle, "sha256": digest}).decode("utf-8")
        row = BuilderAssignment(id=payload.assignment_id, task_id=task.id, base_commit=payload.base_commit,
                                image_id=payload.image_id, bundle_sha256=digest, status="queued", created_at=now())
        db.add(row)
        db.add(BuilderEvent(kind="review_ready", msg="Authorized literal replacement prepared",
                            meta_json=_canonical({"task_id": task.id, "sha256": digest}).decode("utf-8")))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Assignment ID already used") from None
    return view(row)


@router.post("/claim", dependencies=[Depends(require_runner)])
def claim(db: Session = Depends(get_db)):
    if _emergency_stop_active(db):
        raise HTTPException(503, "Builder assignment runner paused")
    at = now()
    row = db.scalar(select(BuilderAssignment).where(or_(
        BuilderAssignment.status == "queued",
        (BuilderAssignment.status == "leased") & (BuilderAssignment.lease_until <= at),
    )).order_by(BuilderAssignment.created_at, BuilderAssignment.id).with_for_update(skip_locked=True).limit(1))
    if row is None:
        return {"status": "idle"}
    if row.claim_count >= MAX_LEASE_CLAIMS:
        row.status = "lease_exhausted"
        row.lease_until = None
        db.commit()
        return view(row)
    task = db.get(BuilderTask, row.task_id)
    try:
        if task is None or task.status != "review_ready":
            raise HTTPException(409, "Candidate is unavailable")
        candidate, _ = _review_bundle(task)
        if candidate["sha256"] != row.bundle_sha256:
            raise HTTPException(409, "Candidate changed after assignment")
    except HTTPException:
        row.status = "superseded"
        db.commit()
        return view(row)
    row.status = "leased"
    row.claim_count += 1
    row.lease_id = uuid4()
    row.lease_until = at + timedelta(minutes=15)
    db.commit()
    return {**view(row), "lease_id": row.lease_id, "review": {
        **candidate, "status": "review_ready", "source_modified": False, "tests_verified": False, "deployed": False,
    }}


@router.post("/{assignment_id}/receipt", dependencies=[Depends(require_runner)])
def submit(assignment_id: UUID, payload: TestReceipt, db: Session = Depends(get_db)):
    row = db.get(BuilderAssignment, assignment_id, with_for_update=True)
    if row is None:
        raise HTTPException(404, "Builder assignment not found")
    data = payload.model_dump(mode="json")
    if row.receipt == data:
        return view(row)
    if (row.status != "leased" or row.lease_id != payload.lease_id or row.lease_until <= now()
            or (row.base_commit, row.image_id, row.bundle_sha256) !=
               (payload.base_commit, payload.image_id, payload.bundle_sha256)):
        raise HTTPException(409, "Receipt does not match the current assignment lease")
    if ((payload.status == "suite_exited_zero" and payload.exit_code != 0)
            or (payload.status == "suite_exited_nonzero" and payload.exit_code not in {1, 2, 3, 4, 5})):
        raise HTTPException(422, "Test runner status differs from the recorded exit code")
    row.receipt = data
    row.status = "review_ready" if payload.status == "suite_exited_zero" else "test_failed"
    db.commit()
    return view(row)


@router.get("/{assignment_id}", dependencies=[Depends(require_prime_control_key)])
def read(assignment_id: UUID, db: Session = Depends(get_db)):
    row = db.get(BuilderAssignment, assignment_id)
    if row is None:
        raise HTTPException(404, "Builder assignment not found")
    return view(row)
