"""SANDBOX activity feed and human labeling router."""
from __future__ import annotations

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_builder_key
from app.models.sandbox_event import SandboxEvent
from app.models.sandbox_human_label import HumanLabel, HumanLabelValue

router = APIRouter(prefix="/sandbox", tags=["sandbox"])


@router.get("/activity")
def sandbox_activity(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """Get SANDBOX activity feed (what the system is doing/blocking)."""
    rows = (
        db.query(SandboxEvent)
        .order_by(SandboxEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "engine_name": r.engine_name,
            "event_type": r.event_type,
            "payload": json.loads(r.payload_json) if r.payload_json else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post("/labels")
def create_label(
    payload: dict,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Create a human label for closed-loop learning.
    
    payload:
      engine_name: "wholesaling"
      lead_ref: "lead_123"  (or any reference)
      label: "APPROVE" | "REJECT" | "NEEDS_INFO"
      notes: optional explanation
    """
    engine_name = payload.get("engine_name") or "wholesaling"
    label = payload.get("label")
    if label not in {v.value for v in HumanLabelValue}:
        raise HTTPException(status_code=400, detail="Invalid label")

    row = HumanLabel(
        engine_name=engine_name,
        lead_ref=payload.get("lead_ref"),
        label=label,
        notes=payload.get("notes"),
    )
    db.add(row)

    # Log as a sandbox event (visibility)
    ev = SandboxEvent(
        engine_name=engine_name,
        event_type="HUMAN_LABEL_CREATED",
        payload_json=json.dumps({"lead_ref": row.lead_ref, "label": label, "notes": row.notes}),
    )
    db.add(ev)
    db.commit()

    return {"ok": True, "engine_name": engine_name, "label": label}
