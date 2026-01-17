"""
Reports router for summary metrics and analytics.
Provides read-only endpoints for monitoring research system health.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.db import get_db
from ..models.research import ResearchSource, ResearchDoc

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
    sources = db.query(ResearchSource).count()
    docs = db.query(ResearchDoc).count()
    embedded = db.query(ResearchDoc).filter(ResearchDoc.embedding_json.isnot(None)).count()
    coverage = (embedded / docs) if docs else 0.0
    
    return {
        "ok": True,
        "sources": sources,
        "docs": docs,
        "embedded": embedded,
        "embedding_coverage": round(coverage, 4)
    }
