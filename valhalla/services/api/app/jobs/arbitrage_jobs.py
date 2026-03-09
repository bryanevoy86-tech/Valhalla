from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_builder_key

router = APIRouter(prefix="/jobs/arbitrage", tags=["jobs"])


@router.post("/scan")
def job_scan(
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """Scan job: detect and log arbitrage opportunities (SIM only)."""
    from app.engines.arbitrage.engine import scan_arbitrage, ArbitragePolicy
    
    policy = ArbitragePolicy()
    return scan_arbitrage(db, policy)

