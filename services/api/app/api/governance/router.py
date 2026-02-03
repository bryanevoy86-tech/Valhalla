"""
Governance API - engine promotion endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_builder_key
from app.models.engine_readiness import EngineReadiness
from app.governance.engine_rules import ENGINE_RULES, PROMOTION_ORDER
from app.jobs.engine_readiness_job import evaluate_engine_readiness

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/engines/readiness")
def list_engine_readiness(db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """
    List all engines and their current readiness state.
    """
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
    
    Returns evaluation results (may transition from SANDBOX → READY).
    """
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
    """
    Manually promote engine from READY → LIVE.
    
    This is a rare operation. Normally happens automatically during evaluation,
    but this endpoint allows manual override when you're confident.
    
    Preconditions:
    - Engine must be in READY state
    - Wholesaling must be LIVE before arbitrage
    """
    row = db.query(EngineReadiness).filter_by(engine_name=engine_name).first()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Engine not found: {engine_name}")
    
    if row.state != "READY":
        raise HTTPException(
            status_code=409,
            detail=f"Engine not READY (current state: {row.state}). Evaluate first.",
        )
    
    # Enforce promotion order
    if engine_name == "arbitrage":
        wholesaling = db.query(EngineReadiness).filter_by(engine_name="wholesaling").first()
        if not wholesaling or wholesaling.state != "LIVE":
            raise HTTPException(
                status_code=409,
                detail="Arbitrage cannot go LIVE until wholesaling is LIVE",
            )
    
    if engine_name == "trading_advisory":
        arbitrage = db.query(EngineReadiness).filter_by(engine_name="arbitrage").first()
        if not arbitrage or arbitrage.state != "LIVE":
            raise HTTPException(
                status_code=409,
                detail="Trading advisory cannot go LIVE until arbitrage is LIVE",
            )
    
    row.state = "LIVE"
    db.add(row)
    db.commit()
    db.refresh(row)
    
    return {
        "ok": True,
        "engine": engine_name,
        "new_state": row.state,
        "message": f"{engine_name} promoted to LIVE",
    }


@router.post("/engines/{engine_name}/sandbox")
def sandbox_engine(
    engine_name: str,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Move engine back to SANDBOX mode for testing.
    
    Use when you want to test changes without affecting production.
    """
    row = db.query(EngineReadiness).filter_by(engine_name=engine_name).first()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Engine not found: {engine_name}")
    
    row.state = "SANDBOX"
    db.add(row)
    db.commit()
    db.refresh(row)
    
    return {
        "ok": True,
        "engine": engine_name,
        "new_state": row.state,
        "message": f"{engine_name} reverted to SANDBOX",
    }


@router.post("/engines/{engine_name}/disable")
def disable_engine(
    engine_name: str,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Disable an engine completely.
    
    Used for emergency shutdown or when disabling a broken feature.
    """
    row = db.query(EngineReadiness).filter_by(engine_name=engine_name).first()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Engine not found: {engine_name}")
    
    row.state = "DISABLED"
    db.add(row)
    db.commit()
    db.refresh(row)
    
    return {
        "ok": True,
        "engine": engine_name,
        "new_state": row.state,
        "message": f"{engine_name} disabled",
    }
