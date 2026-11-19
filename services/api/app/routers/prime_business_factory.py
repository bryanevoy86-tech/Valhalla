"""Heimdall Prime Business Factory pilot API.

Every endpoint requires an independently configured owner operations key.
This pilot creates only INTERNAL listing drafts: no external publishing,
payments, messaging, or owner money movement.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.prime_business_execution import (
    require_factory_key,
    submit_listing_draft,
    approve_action,
    run_one_approved_draft,
    action_status,
)

REQUIRED_TABLES = {
    "legacy_instance_registry_items",
    "legacy_instance_work_items",
    "legacy_orchestration_events",
    "media_contents",
}


def require_factory_schema(db: Session = Depends(get_db)) -> None:
    """Explicit fail-closed schema gate; no DDL on API requests."""
    tables = set(inspect(db.get_bind()).get_table_names(schema="public" if db.bind.dialect.name == "postgresql" else None))
    missing = sorted(REQUIRED_TABLES - tables)
    if missing:
        raise HTTPException(
            status_code=503,
            detail={"error": "BUSINESS_FACTORY_SCHEMA_NOT_READY", "missing_tables": missing},
        )


router = APIRouter(
    prefix="/api/business-factory",
    tags=["business-factory"],
    dependencies=[Depends(require_factory_key), Depends(require_factory_schema)],
)


class ListingDraftRequest(BaseModel):
    legacy_instance_id: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    business_id: str = Field(min_length=3, max_length=120, pattern=r"^[A-Za-z0-9_-]+$")
    engine_id: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    industry: str = Field(min_length=3, max_length=120)
    jurisdiction: str = Field(min_length=2, max_length=80)
    product_id: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    title: str = Field(min_length=8, max_length=120)
    description: str = Field(min_length=40, max_length=1800)
    price_cents_cad: int = Field(ge=1, le=10_000_000)
    request_key: str = Field(min_length=8, max_length=80)


class ApprovalRequest(BaseModel):
    confirmation: str = Field(pattern=r"^APPROVE_INTERNAL_DRAFT$")


@router.post("/listing-drafts")
def queue_listing(request: ListingDraftRequest, db: Session = Depends(get_db)):
    return submit_listing_draft(db, request)


@router.post("/actions/{action_id}/approve")
def approve_internal_draft(
    action_id: str,
    request: ApprovalRequest,
    db: Session = Depends(get_db),
):
    return approve_action(db, action_id, request.confirmation)


@router.post("/actions/run-once")
def execute_one_owner_approved_task(db: Session = Depends(get_db)):
    return run_one_approved_draft(db)


@router.get("/actions/{action_id}")
def get_action_status(action_id: str, db: Session = Depends(get_db)):
    return action_status(db, action_id)
