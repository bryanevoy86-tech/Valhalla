"""
Reports router for summary metrics and analytics.
Provides read-only endpoints for monitoring research system health.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.db import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """
    Get summary statistics for the research system.
    
    Returns:
        - sources: Total number of research sources
        - docs: Total number of research documents
        - embedded: Number of documents with embeddings
        - embedding_coverage: Percentage of docs with embeddings (0.0-1.0)
    """
    try:
        from ..models.research import ResearchSource, ResearchDoc
        sources = db.query(ResearchSource).count()
        docs = db.query(ResearchDoc).count()
        embedded = db.query(ResearchDoc).filter(ResearchDoc.embedding_json.isnot(None)).count()
        coverage = (embedded / docs) if docs else 0.0
    except Exception:
        # If research models don't exist, return zeros
        sources = docs = embedded = 0
        coverage = 0.0
    
    return {
        "ok": True,
        "sources": sources,
        "docs": docs,
        "embedded": embedded,
        "embedding_coverage": round(coverage, 4)
    }


# VA Intake Reporting Endpoints

@router.get("/va-leads-summary")
def get_leads_summary(db: Session = Depends(get_db)):
    """Get summary statistics for VA leads."""
    try:
        from app.services.reporting_simple import get_va_leads_summary
        result = get_va_leads_summary(db)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/approval-summary")
def get_approvals_summary(db: Session = Depends(get_db)):
    """Get summary of approval workflow metrics."""
    try:
        from app.services.reporting_simple import get_approval_summary
        result = get_approval_summary(db)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/eia-monthly-summary")
def get_eia_summary(year: int = None, month: int = None, db: Session = Depends(get_db)):
    """Get EIA monthly summary."""
    try:
        from app.services.reporting_simple import get_eia_monthly_summary
        result = get_eia_monthly_summary(db, year, month)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
