from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..jobs.research_jobs import ingest_all_enabled
from ..jobs.embed_jobs import embed_missing_docs
from ..jobs.forecast_jobs import forecast_month_ahead
from ..jobs.freeze_jobs import check_drawdown

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/research/ingest_all")
def run_ingest_all(
    background_tasks: BackgroundTasks,
    _: bool = Depends(require_builder_key),
    db: Session = Depends(get_db)
):
    """
    Trigger ingestion of all enabled research sources.
    Runs in background to avoid timeout on large ingestion jobs.
    Requires X-API-Key authentication.
    """
    # Run the job in the background so we return immediately
    background_tasks.add_task(ingest_all_enabled)
    
    return {
        "ok": True,
        "job": "research.ingest_all",
        "status": "started",
        "message": "Ingestion job started in background"
    }


@router.post("/research/ingest_all_sync")
def run_ingest_all_sync(
    _: bool = Depends(require_builder_key),
    db: Session = Depends(get_db)
):
    """
    Synchronously trigger ingestion of all enabled research sources.
    Use this for testing or when you need immediate results.
    May timeout on large jobs - prefer /ingest_all for production.
    Requires X-API-Key authentication.
    """
    result = ingest_all_enabled()
    return result


@router.post("/research/embed_missing")
def run_embed_missing(
    _: bool = Depends(require_builder_key)
):
    """
    Generate embeddings for all research docs that don't have them yet.
    Uses local deterministic embeddings by default (EMBEDDING_PROVIDER=local).
    Processes up to 200 docs per call to avoid timeouts.
    Requires X-API-Key authentication.
    
    Returns:
        {"ok": true, "embedded": <count>}
    """
    n = embed_missing_docs()
    return {"ok": True, "embedded": n}


@router.get("/forecast/month")
def run_forecast_month(
    _: bool = Depends(require_builder_key),
    db: Session = Depends(get_db)
):
    """
    Calculate projected balance one month ahead based on forecast yield.
    Uses FORECAST_MONTHLY_YIELD setting (default 4%).
    Requires X-API-Key authentication.
    
    Returns:
        {"ok": true, "current_total": <float>, "forecast_yield": <float>, "projected_balance": <float>}
    """
    result = forecast_month_ahead(db)
    return result


@router.get("/freeze/check")
def run_freeze_check(
    prev_balance: float,
    current_balance: float,
    _: bool = Depends(require_builder_key)
):
    """
    Check if drawdown exceeds freeze threshold.
    Uses FREEZE_DRAWDOWN_PCT setting (default 2%).
    Requires X-API-Key authentication.
    
    Query params:
        prev_balance: Previous balance to compare against
        current_balance: Current balance to check
    
    Returns:
        {"ok": true, "frozen": <bool>, "drawdown_pct": <float>, "threshold_pct": <float>}
    """
    result = check_drawdown(prev_balance, current_balance)
    return result
