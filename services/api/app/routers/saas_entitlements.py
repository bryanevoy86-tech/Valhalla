"""Identity-bound internal trials for explicitly licensed subordinate modules."""
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.saas_access import SaaSPlan, SaaSPlanModule, SaaSTenantEntitlement
from app.routers.auth_weweb import get_current_user
from app.services.prime_business_execution import require_owner_mandate_key
from app.users.models import AccountSettings, UserProfile


Module = Literal["wholesale_engine", "dispo_engine"]
router = APIRouter(prefix="/saas/tenant-entitlements", tags=["saas-entitlements"])
owner = [Depends(require_prime_control_key), Depends(require_owner_mandate_key)]


class TrialIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entitlement_id: UUID
    tenant_id: UUID
    subject_id: int = Field(gt=0, strict=True)
    plan_id: int = Field(gt=0)
    expires_at: datetime
    modules: set[Module] = Field(min_length=1, max_length=2)


def _ready(db):
    if not inspect(db.connection()).has_table(SaaSTenantEntitlement.__tablename__):
        raise HTTPException(503, "Tenant trial schema unavailable")


def _utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _active_identity(db, user_id):
    return db.scalar(select(UserProfile).join(AccountSettings, AccountSettings.user_id == UserProfile.user_id)
                     .where(UserProfile.user_id == user_id, AccountSettings.account_locked.is_(False)))


def _trial(row):
    return {
        "entitlement_id": row.id, "tenant_id": row.tenant_id, "modules": row.modules,
        "expires_at": row.expires_at.replace(tzinfo=timezone.utc), "revoked": row.revoked_at is not None,
        "basis": "INTERNAL_TRIAL", "payment_verified": False,
    }


@router.post("", status_code=201, dependencies=owner)
def create_trial(payload: TrialIn, db: Session = Depends(get_db)):
    _ready(db)
    if payload.expires_at.utcoffset() is None:
        raise HTTPException(422, "Expiry must include a UTC offset")
    expires = payload.expires_at.astimezone(timezone.utc).replace(tzinfo=None)
    modules = sorted(payload.modules)
    row = db.get(SaaSTenantEntitlement, payload.entitlement_id)
    if row is not None:
        if (row.tenant_id, row.subject_id, row.plan_id, row.expires_at, row.modules) != (
            payload.tenant_id, payload.subject_id, payload.plan_id, expires, modules,
        ):
            raise HTTPException(409, "Tenant entitlement ID already used")
        return _trial(row)
    if expires <= _utc():
        raise HTTPException(422, "Trial expiry must be in the future")
    profile = _active_identity(db, payload.subject_id)
    plan = db.get(SaaSPlan, payload.plan_id)
    if profile is None or plan is None or not plan.is_active:
        raise HTTPException(409, "An active identity and plan are required")
    allowed = set(db.scalars(select(SaaSPlanModule.module_key).filter_by(plan_id=plan.id)).all())
    if not payload.modules <= allowed:
        raise HTTPException(409, "Plan does not contain the requested modules")
    row = SaaSTenantEntitlement(id=payload.entitlement_id, tenant_id=payload.tenant_id,
                               subject_id=payload.subject_id, plan_id=payload.plan_id,
                               expires_at=expires, modules=modules)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Tenant entitlement ID already used") from None
    return _trial(row)


@router.delete("/{entitlement_id}", dependencies=owner)
def revoke_trial(entitlement_id: UUID, db: Session = Depends(get_db)):
    _ready(db)
    row = db.get(SaaSTenantEntitlement, entitlement_id, with_for_update=True)
    if row is None:
        raise HTTPException(404, "Trial entitlement not found")
    if row.revoked_at is None:
        row.revoked_at = _utc()
        db.commit()
    return _trial(row)


@router.get("/{tenant_id}/access/{module_key}")
def access(tenant_id: UUID, module_key: Module, principal: dict = Depends(get_current_user),
           db: Session = Depends(get_db)):
    _ready(db)
    if type(principal["user_id"]) is not int:
        raise HTTPException(401, "Subscriber identity unavailable")
    profile = _active_identity(db, principal["user_id"])
    if profile is None or profile.email != principal.get("sub"):
        raise HTTPException(401, "Subscriber identity unavailable")
    trial = SaaSTenantEntitlement
    candidates = db.scalars(select(trial).join(SaaSPlan, SaaSPlan.id == trial.plan_id).join(
        SaaSPlanModule, SaaSPlanModule.plan_id == trial.plan_id,
    ).where(trial.tenant_id == tenant_id, trial.subject_id == profile.user_id, trial.expires_at > _utc(),
            trial.revoked_at.is_(None), SaaSPlan.is_active.is_(True), SaaSPlanModule.module_key == module_key
            ).order_by(trial.expires_at.desc())).all()
    for row in candidates:
        if module_key in row.modules:
            return {**_trial(row), "has_access": True, "module_key": module_key}
    from app.heimdall.authority import is_live
    from app.services.stripe_recurring import paid_module_access

    paid = paid_module_access(db, tenant_id, module_key, principal, live=is_live())
    if paid is not None:
        return paid
    raise HTTPException(404, "Tenant module entitlement not found")
