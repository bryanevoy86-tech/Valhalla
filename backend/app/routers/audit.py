from typing import Optional

from backend.app.deps.tenant import get_db, org_membership
from backend.app.models.audit_log import AuditLog
from backend.app.services.audit import json_diff
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import String
from sqlalchemy.orm import Session

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit(
    entity: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="free text in meta"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    ctx=Depends(org_membership(["viewer", "operator", "admin", "owner"])),
    db: Session = Depends(get_db),
):
    qry = db.query(AuditLog).filter((AuditLog.org_id == ctx["org_id"]) | (AuditLog.org_id == None))
    if entity:
        qry = qry.filter(AuditLog.entity == entity)
    if entity_id:
        qry = qry.filter(AuditLog.entity_id == str(entity_id))
    if action:
        qry = qry.filter(AuditLog.action == action)
    if q:
        qry = qry.filter(AuditLog.meta.cast(String).ilike(f"%{q}%"))
    total = qry.count()
    rows = qry.order_by(AuditLog.created_at.desc()).offset((page - 1) * size).limit(size).all()

    def to_dict(r: AuditLog):
        return {
            "id": r.id,
            "when": r.created_at,
            "actor_user_id": r.actor_user_id,
            "action": r.action,
            "entity": r.entity,
            "entity_id": r.entity_id,
            "route": r.route,
            "ip": r.ip,
            "diff": json_diff(r.before, r.after),
            "meta": r.meta,
        }

    return {"total": total, "items": [to_dict(r) for r in rows], "page": page, "size": size}


@router.get("/{audit_id}")
def get_audit(audit_id: int, ctx=Depends(org_membership()), db: Session = Depends(get_db)):
    r = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    if not r or (r.org_id not in (None, ctx["org_id"])):
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": r.id,
        "before": r.before,
        "after": r.after,
        "diff": json_diff(r.before, r.after),
        "meta": r.meta,
        "actor_user_id": r.actor_user_id,
        "when": r.created_at,
    }
