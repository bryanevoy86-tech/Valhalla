"""
Engine activation guard - enforces that only LIVE engines execute real-world effects.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.engine_readiness import EngineReadiness


def require_engine_live(db: Session, engine_name: str):
    """
    Guard: Only allow execution if engine is LIVE.
    
    Raises HTTPException if engine is not in LIVE state.
    """
    row = db.query(EngineReadiness).filter_by(engine_name=engine_name).first()
    
    if not row:
        raise HTTPException(
            status_code=409,
            detail={
                "title": "EngineNotFound",
                "message": f"Engine '{engine_name}' not found in readiness registry",
            },
        )
    
    if row.state != "LIVE":
        raise HTTPException(
            status_code=409,
            detail={
                "title": "EngineNotLive",
                "message": f"Engine '{engine_name}' not LIVE (current state: {row.state})",
                "current_state": row.state,
            },
        )
