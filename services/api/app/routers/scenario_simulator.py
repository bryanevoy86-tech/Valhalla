"""
PACK AI: Scenario Simulator Router
Prefix: /scenarios
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.scenario_simulator import (
    ScenarioCreate,
    ScenarioOut,
    ScenarioRunCreate,
    ScenarioRunUpdate,
    ScenarioRunOut,
)
from app.services.scenario_simulator import (
    create_scenario,
    list_scenarios,
    get_scenario_by_key,
    create_run,
    update_run,
    list_runs_for_scenario,
)

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.post("/", response_model=ScenarioOut)
def create_scenario_endpoint(
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
):
    """Create a new scenario"""
    return create_scenario(db, payload)


@router.get("/", response_model=List[ScenarioOut])
def list_scenarios_endpoint(
    db: Session = Depends(get_db),
):
    """List all scenarios"""
    return list_scenarios(db)


@router.get("/by-key/{key}", response_model=ScenarioOut)
def get_scenario_by_key_endpoint(
    key: str,
    db: Session = Depends(get_db),
):
    """Get a scenario by its key"""
    obj = get_scenario_by_key(db, key)
    if not obj:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return obj


@router.post("/runs", response_model=ScenarioRunOut)
def create_run_endpoint(
    payload: ScenarioRunCreate,
    db: Session = Depends(get_db),
):
    """Create a new scenario run (queueing a simulation)"""
    run = create_run(db, payload)
    # At this point you could enqueue a worker job to actually run the scenario.
    return run


@router.patch("/runs/{run_id}", response_model=ScenarioRunOut)
def update_run_endpoint(
    run_id: int,
    payload: ScenarioRunUpdate,
    db: Session = Depends(get_db),
):
    """Update a scenario run with results and status"""
    obj = update_run(db, run_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Run not found")
    return obj


@router.get("/runs/by-scenario/{scenario_id}", response_model=List[ScenarioRunOut])
def list_runs_for_scenario_endpoint(
    scenario_id: int,
    db: Session = Depends(get_db),
):
    """List all runs for a specific scenario"""
    return list_runs_for_scenario(db, scenario_id)
