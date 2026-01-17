"""
PACK AI: Scenario Simulator Service
"""

import json
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.scenario_simulator import Scenario, ScenarioRun
from app.schemas.scenario_simulator import ScenarioCreate, ScenarioRunCreate, ScenarioRunUpdate


def create_scenario(db: Session, payload: ScenarioCreate) -> Scenario:
    """Create a new scenario"""
    obj = Scenario(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_scenarios(db: Session) -> List[Scenario]:
    """List all scenarios"""
    return db.query(Scenario).order_by(Scenario.created_at.desc()).all()


def get_scenario_by_key(db: Session, key: str) -> Optional[Scenario]:
    """Get a scenario by its unique key"""
    return db.query(Scenario).filter(Scenario.key == key).first()


def create_run(db: Session, payload: ScenarioRunCreate) -> ScenarioRun:
    """Create a new scenario run"""
    obj = ScenarioRun(
        scenario_id=payload.scenario_id,
        input_payload=json.dumps(payload.input_payload),
        status="pending",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_run(
    db: Session,
    run_id: int,
    payload: ScenarioRunUpdate,
) -> Optional[ScenarioRun]:
    """Update a scenario run with results"""
    obj = db.query(ScenarioRun).filter(ScenarioRun.id == run_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)

    if "status" in data:
        obj.status = data["status"]
        if data["status"] in ("completed", "failed"):
            obj.completed_at = datetime.utcnow()

    if "result_payload" in data and data["result_payload"] is not None:
        obj.result_payload = json.dumps(data["result_payload"])

    if "error_message" in data:
        obj.error_message = data["error_message"]

    db.commit()
    db.refresh(obj)
    return obj


def list_runs_for_scenario(db: Session, scenario_id: int) -> List[ScenarioRun]:
    """List all runs for a specific scenario"""
    return (
        db.query(ScenarioRun)
        .filter(ScenarioRun.scenario_id == scenario_id)
        .order_by(ScenarioRun.created_at.desc())
        .all()
    )
