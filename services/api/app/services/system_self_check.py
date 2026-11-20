"""Inspect persisted integrity signals without invoking workers or providers."""

import json
import os

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.completion_registry import LearningTaskQueueItem
from app.models.go_live_state import GoLiveState


def run_system_self_check(db: Session, *, record_alerts: bool = False) -> dict:
    release = db.get(GoLiveState, 1)
    emergency_stop = os.getenv("VALHALLA_EMERGENCY_STOP", "").strip().lower() in {
        "1", "true", "yes", "on",
    }
    kill_switch = release is not None and release.kill_switch_engaged
    blocked_learning = db.scalar(
        select(func.count()).select_from(LearningTaskQueueItem)
        .where(LearningTaskQueueItem.status == "blocked")
    )
    signals = {}
    if emergency_stop:
        signals["emergency_stop"] = "Emergency stop is configured"
    if kill_switch:
        signals["kill_switch"] = "Persisted kill switch is engaged"
    if release is None:
        signals["release_state_missing"] = "Release control record is missing"
    if blocked_learning:
        signals["learning_queue_blocked"] = f"{blocked_learning} learning tasks are blocked"

    if record_alerts and signals:
        db.add(AuditLog(
            event_type="integrity_alert",
            event_source="system",
            message="Integrity check detected operational blockers",
            event_data=json.dumps(signals, sort_keys=True),
        ))
        db.commit()

    return {
        "anomaly_detection": {
            "state": "ANOMALY_DETECTED" if signals else "NO_ANOMALY_IN_CHECKED_SIGNALS",
            "signals": signals,
        },
        "fail_safe_state": {"active": bool(emergency_stop or kill_switch)},
        "integrity_audit_trail": {"events_emitted": int(record_alerts and bool(signals))},
    }
