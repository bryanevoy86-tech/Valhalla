"""SANDBOX activity feed and human labeling router."""
from __future__ import annotations

import json
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_builder_key
from app.models.sandbox_event import SandboxEvent
from app.models.sandbox_human_label import HumanLabel, HumanLabelValue
from app.models.pending_action import PendingAction, PendingActionStatus

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


# === LEARNING METRICS ENDPOINTS ===

@router.get("/learning/report")
def learning_report(
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """Get comprehensive SANDBOX learning metrics."""
    
    pending = db.query(PendingAction).filter(PendingAction.status == PendingActionStatus.PENDING.value).count()
    approved = db.query(PendingAction).filter(PendingAction.status == PendingActionStatus.APPROVED.value).count()
    declined = db.query(PendingAction).filter(PendingAction.status == PendingActionStatus.DECLINED.value).count()
    executed = db.query(PendingAction).filter(PendingAction.status == PendingActionStatus.EXECUTED.value).count()
    failed = db.query(PendingAction).filter(PendingAction.status == PendingActionStatus.FAILED.value).count()
    
    total_decided = approved + declined
    approval_rate = (approved / total_decided) if total_decided > 0 else None
    fp_rate = (declined / total_decided) if total_decided > 0 else None
    
    # Event breakdown
    event_breakdown = db.query(
        SandboxEvent.event_type,
        func.count(SandboxEvent.id).label("count")
    ).group_by(SandboxEvent.event_type).order_by(func.count(SandboxEvent.id).desc()).all()
    
    events = {event[0]: event[1] for event in event_breakdown}
    
    # Label distribution
    label_breakdown = db.query(
        HumanLabel.label,
        func.count(HumanLabel.id).label("count")
    ).group_by(HumanLabel.label).all()
    
    labels = {label[0]: label[1] for label in label_breakdown}
    total_labels = sum(labels.values())
    
    # Trend (last 24h)
    now = dt.datetime.now(dt.timezone.utc)
    yesterday = now - dt.timedelta(days=1)
    
    recent_approved = db.query(PendingAction).filter(
        PendingAction.reviewed_at >= yesterday,
        PendingAction.status == PendingActionStatus.APPROVED.value
    ).count()
    
    recent_declined = db.query(PendingAction).filter(
        PendingAction.reviewed_at >= yesterday,
        PendingAction.status == PendingActionStatus.DECLINED.value
    ).count()
    
    recent_decided = recent_approved + recent_declined
    
    return {
        "timestamp": now.isoformat(),
        "queue": {
            "pending": pending,
            "approved": approved,
            "declined": declined,
            "executed": executed,
            "failed": failed,
        },
        "quality": {
            "total_decided": total_decided,
            "approval_rate": approval_rate,
            "false_positive_rate": fp_rate,
            "interpretation": (
                "Strong (70%+)" if approval_rate and approval_rate >= 0.7 else
                "Moderate (50-70%)" if approval_rate and approval_rate >= 0.5 else
                "Needs tuning (<50%)" if approval_rate else
                "No data"
            )
        },
        "safety": {
            "false_positives": declined,
            "fp_rate": fp_rate,
            "status": "Safe" if fp_rate == 0 or fp_rate is None else (
                "Good" if fp_rate < 0.1 else
                "Alert" if fp_rate < 0.2 else
                "Review"
            )
        },
        "events": {
            "total": sum(events.values()),
            "breakdown": events,
        },
        "learning": {
            "total_labels": total_labels,
            "distribution": labels,
            "signal_strength": (
                "Strong (20+)" if total_labels >= 20 else
                "Moderate (5-20)" if total_labels >= 5 else
                "Weak (<5)" if total_labels > 0 else
                "None"
            ),
            "recommendation": (
                "Ready to retrain" if total_labels >= 20 else
                f"Label {20 - total_labels} more items to reach training threshold" if total_labels > 0 else
                "Start labeling items"
            )
        },
        "trend_24h": {
            "decisions_made": recent_decided,
            "items_approved": recent_approved,
            "items_declined": recent_decided - recent_approved,
        },
        "system_health": {
            "queue_size": pending,
            "processing_speed": "Active" if recent_decided > 0 else "Idle",
            "learning_active": total_labels > 0,
            "safety_status": "Green" if (fp_rate == 0 or fp_rate is None) else "Yellow" if fp_rate < 0.2 else "Red",
        }
    }


@router.get("/learning/scorecard")
def learning_scorecard(
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """Get simplified scorecard for tracking progress."""
    report = learning_report(db=db, _=_)
    
    return {
        "date": report["timestamp"].split("T")[0],
        "metrics": {
            "items_queued": report["queue"]["pending"],
            "items_approved": report["queue"]["approved"],
            "items_declined": report["queue"]["declined"],
            "approval_rate": f"{(report['quality']['approval_rate'] * 100):.1f}%" if report['quality']['approval_rate'] is not None else "N/A",
            "false_positive_rate": f"{(report['safety']['fp_rate'] * 100):.1f}%" if report['safety']['fp_rate'] is not None else "0%",
            "labels_collected": report["learning"]["total_labels"],
            "decisions_24h": report["trend_24h"]["decisions_made"],
        },
        "status": report["system_health"]["safety_status"],
        "learning_recommendation": report["learning"]["recommendation"],
    }
