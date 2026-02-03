"""Pending action approvals/decline router."""
from __future__ import annotations

import json
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_builder_key
from app.models.pending_action import PendingAction, PendingActionStatus
from app.models.sandbox_event import SandboxEvent

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/pending")
def list_pending(
    engine_name: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """List pending actions (queued real-world effects waiting for approval in SANDBOX)."""
    q = db.query(PendingAction).filter(PendingAction.status == PendingActionStatus.PENDING.value)
    if engine_name:
        q = q.filter(PendingAction.engine_name == engine_name)
    rows = q.order_by(PendingAction.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "engine_name": r.engine_name,
            "action_type": r.action_type,
            "status": r.status,
            "target": r.target,
            "subject": r.subject,
            "preview_text": r.preview_text,
            "payload": json.loads(r.payload_json) if r.payload_json else None,
            "reason": r.reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/decided")
def list_decided(
    engine_name: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """List decided actions (APPROVED or DECLINED) for analysis."""
    q = db.query(PendingAction).filter(
        PendingAction.status.in_([PendingActionStatus.APPROVED.value, PendingActionStatus.DECLINED.value])
    )
    if engine_name:
        q = q.filter(PendingAction.engine_name == engine_name)
    rows = q.order_by(PendingAction.reviewed_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "engine_name": r.engine_name,
            "action_type": r.action_type,
            "status": r.status,
            "target": r.target,
            "subject": r.subject,
            "preview_text": r.preview_text,
            "payload": json.loads(r.payload_json) if r.payload_json else None,
            "reason": r.reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        }
        for r in rows
    ]


@router.post("/{action_id}/approve")
def approve_action(
    action_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """Approve a pending action."""
    row = db.query(PendingAction).get(action_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    if row.status != PendingActionStatus.PENDING.value:
        raise HTTPException(status_code=409, detail=f"Not pending (status={row.status})")

    row.status = PendingActionStatus.APPROVED.value
    row.reviewed_at = dt.datetime.now(dt.timezone.utc)

    db.add(SandboxEvent(
        engine_name=row.engine_name,
        event_type="PENDING_ACTION_APPROVED",
        payload_json=json.dumps({"action_id": row.id, "action_type": row.action_type}),
    ))
    db.commit()
    return {"ok": True, "id": row.id, "status": row.status}


@router.post("/{action_id}/decline")
def decline_action(
    action_id: int,
    payload: dict | None = None,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """Decline a pending action."""
    row = db.query(PendingAction).get(action_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    if row.status != PendingActionStatus.PENDING.value:
        raise HTTPException(status_code=409, detail=f"Not pending (status={row.status})")

    row.status = PendingActionStatus.DECLINED.value
    row.reviewed_at = dt.datetime.now(dt.timezone.utc)

    db.add(SandboxEvent(
        engine_name=row.engine_name,
        event_type="PENDING_ACTION_DECLINED",
        payload_json=json.dumps({"action_id": row.id, "action_type": row.action_type, "notes": (payload or {}).get("notes")}),
    ))
    db.commit()
    return {"ok": True, "id": row.id, "status": row.status}
