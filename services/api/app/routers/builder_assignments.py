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
from app.models.builder import BuilderTask
from app.models.builder_assignment import BuilderAssignment
from app.routers.builder import _review_bundle
from app.services.prime_business_execution import _emergency_stop_active, require_owner_mandate_key


def require_schema(db: Session = Depends(get_db)):
    schema = inspect(db.connection())
    if any(not schema.has_table(model.__tablename__) for model in (BuilderTask, BuilderAssignment)):
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
            "base_commit": row.base_commit, "image_id": row.image_id, "bundle_sha256": row.bundle_sha256,
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
