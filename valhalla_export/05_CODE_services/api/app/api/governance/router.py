"""
Governance API - engine promotion endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_builder_key

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/health")
def governance_health(db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """Health check for governance API."""
    return {"ok": True, "service": "governance"}


@router.get("/engines/readiness")
def list_engine_readiness(db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """
    List all engines and their current readiness state.
    """
    from app.models.engine_readiness import EngineReadiness
    
    engines = db.query(EngineReadiness).all()
    return [
        {
            "engine_name": e.engine_name,
            "state": e.state,
            "approval_rate": e.approval_rate,
            "false_positive_rate": e.false_positive_rate,
            "sample_size": e.sample_size,
            "evaluated_at": e.evaluated_at,
        }
        for e in engines
    ]


@router.post("/engines/{engine_name}/evaluate")
def evaluate_engine(
    engine_name: str,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Evaluate a specific engine for promotion.
    """
    from app.governance.engine_rules import ENGINE_RULES
    from app.jobs.engine_readiness_job import evaluate_engine_readiness
    
    if engine_name not in ENGINE_RULES:
        raise HTTPException(status_code=404, detail=f"Unknown engine: {engine_name}")
    
    results = evaluate_engine_readiness(db, engine_name)
    return {"engine": engine_name, "evaluation": results.get(engine_name, {})}


@router.post("/engines/{engine_name}/promote")
def promote_engine(
    engine_name: str,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """Manually promote engine from READY → LIVE."""
    from app.models.engine_readiness import EngineReadiness
    
    row = db.query(EngineReadiness).filter_by(engine_name=engine_name).first()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Engine not found: {engine_name}")
    
    if row.state != "READY":
        raise HTTPException(
            status_code=409,
            detail=f"Engine not READY (current state: {row.state}).",
        )
    
    row.state = "LIVE"
    db.add(row)
    db.commit()
    db.refresh(row)
    
    return {"ok": True, "engine": engine_name, "new_state": row.state}


@router.post("/engines/{engine_name}/sandbox")
def sandbox_engine(
    engine_name: str,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """Move engine back to SANDBOX mode."""
    from app.models.engine_readiness import EngineReadiness
    
    row = db.query(EngineReadiness).filter_by(engine_name=engine_name).first()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Engine not found: {engine_name}")
    
    row.state = "SANDBOX"
    db.add(row)
    db.commit()
    db.refresh(row)
    
    return {"ok": True, "engine": engine_name, "new_state": row.state}


@router.post("/engines/{engine_name}/disable")
def disable_engine(
    engine_name: str,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """Disable an engine completely."""
    from app.models.engine_readiness import EngineReadiness
    
    row = db.query(EngineReadiness).filter_by(engine_name=engine_name).first()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Engine not found: {engine_name}")
    
    row.state = "DISABLED"
    db.add(row)
    db.commit()
    db.refresh(row)
    
    return {"ok": True, "engine": engine_name, "new_state": row.state}
