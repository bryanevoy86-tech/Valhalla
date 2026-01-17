"""
PACK AL: Brain State Snapshot Service
"""

import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.brain_state import BrainStateSnapshot
from app.schemas.brain_state import BrainStateCreate
from app.services.empire_dashboard import get_empire_dashboard
from app.services.analytics_engine import get_analytics_snapshot
from app.models.scenario_simulator import ScenarioRun


def summarize_recent_scenarios(db: Session, limit: int = 20) -> Dict[str, Any]:
    q = (
        db.query(ScenarioRun)
        .order_by(ScenarioRun.created_at.desc())
        .limit(limit)
        .all()
    )
    runs = []
    for r in q:
        runs.append(
            {
                "id": r.id,
                "scenario_id": r.scenario_id,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
        )
    return {"recent_runs": runs}


def create_brain_state(db: Session, payload: BrainStateCreate) -> BrainStateSnapshot:
    empire = get_empire_dashboard(db)
    analytics = get_analytics_snapshot(db)
    scenarios = summarize_recent_scenarios(db)

    obj = BrainStateSnapshot(
        label=payload.label,
        empire_dashboard_json=json.dumps(empire),
        analytics_snapshot_json=json.dumps(analytics),
        scenarios_summary_json=json.dumps(scenarios),
        created_by=payload.created_by or "heimdall",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_brain_states(db: Session, limit: int = 50) -> List[BrainStateSnapshot]:
    return (
        db.query(BrainStateSnapshot)
        .order_by(BrainStateSnapshot.created_at.desc())
        .limit(limit)
        .all()
    )


def brain_state_to_dict(obj: BrainStateSnapshot) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "label": obj.label,
        "empire_dashboard": json.loads(obj.empire_dashboard_json or "{}"),
        "analytics_snapshot": json.loads(obj.analytics_snapshot_json or "{}"),
        "scenarios_summary": json.loads(obj.scenarios_summary_json or "{}"),
        "created_by": obj.created_by,
        "created_at": obj.created_at.isoformat(),
    }
