"""Learning report router - track SANDBOX learning progress."""
from __future__ import annotations

import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_builder_key
from app.models.pending_action import PendingAction, PendingActionStatus
from app.models.sandbox_event import SandboxEvent
from app.models.sandbox_human_label import HumanLabel, HumanLabelValue

router = APIRouter(prefix="/sandbox/learning", tags=["sandbox-learning"])


@router.get("/report")
def learning_report(
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Get comprehensive SANDBOX learning metrics.
    
    Returns:
    - Queue quality metrics (total, approved, declined, approval rate)
    - Safety metrics (false positive rate)
    - Event breakdown (what's being blocked/logged)
    - Label distribution (learning signal)
    - Trend indicators (is it improving?)
    """
    
    # === METRIC 1: Queue Quality ===
    queue_stats = db.query(
        func.count(PendingAction.id).filter(PendingAction.status == PendingActionStatus.PENDING.value).label("pending"),
        func.count(PendingAction.id).filter(PendingAction.status == PendingActionStatus.APPROVED.value).label("approved"),
        func.count(PendingAction.id).filter(PendingAction.status == PendingActionStatus.DECLINED.value).label("declined"),
        func.count(PendingAction.id).filter(PendingAction.status == PendingActionStatus.EXECUTED.value).label("executed"),
        func.count(PendingAction.id).filter(PendingAction.status == PendingActionStatus.FAILED.value).label("failed"),
    ).first()
    
    pending = db.query(PendingAction).filter(PendingAction.status == PendingActionStatus.PENDING.value).count()
    approved = db.query(PendingAction).filter(PendingAction.status == PendingActionStatus.APPROVED.value).count()
    declined = db.query(PendingAction).filter(PendingAction.status == PendingActionStatus.DECLINED.value).count()
    executed = db.query(PendingAction).filter(PendingAction.status == PendingActionStatus.EXECUTED.value).count()
    failed = db.query(PendingAction).filter(PendingAction.status == PendingActionStatus.FAILED.value).count()
    
    total_decided = approved + declined
    approval_rate = (approved / total_decided) if total_decided > 0 else None
    fp_rate = (declined / total_decided) if total_decided > 0 else None
    
    # === METRIC 2: Event Breakdown ===
    event_breakdown = db.query(
        SandboxEvent.event_type,
        func.count(SandboxEvent.id).label("count")
    ).group_by(SandboxEvent.event_type).order_by(func.count(SandboxEvent.id).desc()).all()
    
    events = {event[0]: event[1] for event in event_breakdown}
    
    # === METRIC 3: Label Distribution (Learning Signal) ===
    label_breakdown = db.query(
        HumanLabel.label,
        func.count(HumanLabel.id).label("count")
    ).group_by(HumanLabel.label).all()
    
    labels = {label[0]: label[1] for label in label_breakdown}
    total_labels = sum(labels.values())
    label_distribution = {
        k: v for k, v in labels.items()
    } if labels else {}
    
    # === METRIC 4: Trend Indicators ===
    # Count actions approved/declined in last 24h vs all-time
    now = dt.datetime.now(dt.timezone.utc)
    yesterday = now - dt.timedelta(days=1)
    
    recent_decided = db.query(PendingAction).filter(
        PendingAction.reviewed_at >= yesterday,
        PendingAction.status.in_([PendingActionStatus.APPROVED.value, PendingActionStatus.DECLINED.value])
    ).count()
    
    recent_approved = db.query(PendingAction).filter(
        PendingAction.reviewed_at >= yesterday,
        PendingAction.status == PendingActionStatus.APPROVED.value
    ).count()
    
    # === ASSEMBLE REPORT ===
    return {
        "timestamp": now.isoformat(),
        "period": "all_time",
        
        # Queue metrics
        "queue": {
            "pending": pending,
            "approved": approved,
            "declined": declined,
            "executed": executed,
            "failed": failed,
        },
        
        # Quality metrics
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
        
        # Safety metrics
        "safety": {
            "false_positives": declined,  # Proxy: declined items
            "fp_rate": fp_rate,
            "status": "Safe" if fp_rate == 0 or fp_rate is None else (
                "Good" if fp_rate < 0.1 else
                "Alert" if fp_rate < 0.2 else
                "Review"
            )
        },
        
        # Event breakdown
        "events": {
            "total": sum(events.values()),
            "breakdown": events,
        },
        
        # Learning signal
        "learning": {
            "total_labels": total_labels,
            "distribution": label_distribution,
            "signal_strength": (
                "Strong (20+)" if total_labels >= 20 else
                "Moderate (5-20)" if total_labels >= 5 else
                "Weak (<5)" if total_labels > 0 else
                "None"
            ),
            "recommendation": (
                "Ready to retrain" if total_labels >= 20 else
                f"Label {20 - total_labels} more items to reach training threshold"
            )
        },
        
        # Trending (last 24h)
        "trend_24h": {
            "decisions_made": recent_decided,
            "items_approved": recent_approved,
            "items_declined": recent_decided - recent_approved,
        },
        
        # Overall health
        "system_health": {
            "queue_size": pending,
            "processing_speed": "Active" if recent_decided > 0 else "Idle",
            "learning_active": total_labels > 0,
            "safety_status": "Green" if (fp_rate == 0 or fp_rate is None) else "Yellow" if fp_rate < 0.2 else "Red",
        }
    }


@router.get("/scorecard")
def learning_scorecard(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Get a simplified scorecard for tracking progress over time.
    
    Good for daily emails or dashboards.
    """
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
