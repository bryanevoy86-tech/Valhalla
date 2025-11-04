from typing import Any, Dict

from app.core.security import create_impersonation_token
from app.deps.auth import get_current_user
from app.deps.tenant import get_db, org_membership
from app.models.feature_flag import AdminAction, FeatureFlag
from app.models.org_member import OrgMember
from app.models.user import User
from app.services.admin import list_feature_flags, log_admin, promote_user_role, set_feature_flag
from app.services.alerts import process_schedules, process_sla
from app.services.notifications import deliver_pending_webhooks
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_org_users(ctx=Depends(org_membership(["owner", "admin"])), db: Session = Depends(get_db)):
    org_id = ctx["org_id"]
    rows = (
        db.query(User, OrgMember)
        .join(OrgMember, OrgMember.user_id == User.id)
        .filter(OrgMember.org_id == org_id)
        .all()
    )
    return [{"id": u.id, "email": u.email, "role": u.role, "org_role": m.role} for (u, m) in rows]


@router.patch("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    payload: Dict[str, Any],
    ctx=Depends(org_membership(["owner", "admin"])),
    db: Session = Depends(get_db),
    actor=Depends(get_current_user),
):
    role = payload.get("role")
    if role not in ["viewer", "operator", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    u = promote_user_role(db, user_id=user_id, role=role)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    log_admin(
        db,
        actor_user_id=actor.id,
        org_id=ctx["org_id"],
        action="promote_user",
        details={"user_id": user_id, "role": role},
    )
    return {"ok": True}


@router.post("/impersonate/{target_user_id}")
def impersonate(
    target_user_id: int,
    ctx=Depends(org_membership(["owner", "admin"])),
    db: Session = Depends(get_db),
    actor=Depends(get_current_user),
):
    mem = (
        db.query(OrgMember)
        .filter(OrgMember.org_id == ctx["org_id"], OrgMember.user_id == target_user_id)
        .first()
    )
    if not mem:
        raise HTTPException(status_code=403, detail="Target user not in org")
    token = create_impersonation_token(
        actor_id=actor.id, target_user_id=target_user_id, expires_minutes=120
    )
    log_admin(
        db,
        actor_user_id=actor.id,
        org_id=ctx["org_id"],
        action="impersonate",
        details={"target_user_id": target_user_id},
    )
    return {"token": token}


@router.get("/flags")
def get_flags(ctx=Depends(org_membership(["owner", "admin"])), db: Session = Depends(get_db)):
    rows = list_feature_flags(db, org_id=ctx["org_id"])
    return [
        {
            "id": r.id,
            "scope": r.scope,
            "key": r.key,
            "enabled": r.enabled,
            "payload": r.payload,
            "org_id": r.org_id,
            "user_id": r.user_id,
        }
        for r in rows
    ]


@router.post("/flags")
def upsert_flag(
    payload: Dict[str, Any],
    ctx=Depends(org_membership(["owner", "admin"])),
    db: Session = Depends(get_db),
    actor=Depends(get_current_user),
):
    scope = payload.get("scope", "org")
    key = payload["key"]
    enabled = bool(payload.get("enabled", True))
    org_id = payload.get("org_id") or (ctx["org_id"] if scope == "org" else None)
    user_id = payload.get("user_id")
    row = set_feature_flag(
        db,
        scope=scope,
        key=key,
        enabled=enabled,
        payload=payload.get("payload"),
        org_id=org_id,
        user_id=user_id,
    )
    log_admin(
        db,
        actor_user_id=actor.id,
        org_id=ctx["org_id"],
        action="toggle_flag",
        details={
            "scope": scope,
            "key": key,
            "enabled": enabled,
            "org_id": org_id,
            "user_id": user_id,
        },
    )
    return {"id": row.id}


@router.delete("/flags/{flag_id}")
def delete_flag(
    flag_id: int,
    ctx=Depends(org_membership(["owner", "admin"])),
    db: Session = Depends(get_db),
    actor=Depends(get_current_user),
):
    row = db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(row)
    db.commit()
    log_admin(
        db,
        actor_user_id=actor.id,
        org_id=ctx["org_id"],
        action="delete_flag",
        details={"flag_id": flag_id},
    )
    return {"ok": True}


@router.post("/maintenance/deliver-webhooks")
def maintenance_deliver(
    ctx=Depends(org_membership(["owner", "admin"])), db: Session = Depends(get_db)
):
    import asyncio

    asyncio.run(deliver_pending_webhooks(db, limit=100))
    return {"ok": True}


@router.post("/maintenance/tick")
def maintenance_tick(
    ctx=Depends(org_membership(["owner", "admin"])), db: Session = Depends(get_db)
):
    n1 = process_schedules(db)
    n2 = process_sla(db)
    return {"processed_schedules": n1, "processed_sla": n2}


@router.get("/actions")
def list_admin_actions(
    limit: int = Query(50, ge=1, le=200),
    ctx=Depends(org_membership(["owner", "admin"])),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(AdminAction)
        .filter((AdminAction.org_id == ctx["org_id"]) | (AdminAction.org_id == None))
        .order_by(AdminAction.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "actor_user_id": r.actor_user_id,
            "org_id": r.org_id,
            "action": r.action,
            "details": r.details,
            "created_at": r.created_at,
        }
        for r in rows
    ]
