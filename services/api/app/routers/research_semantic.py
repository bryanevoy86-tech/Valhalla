"""
Semantic search endpoints for research docs using vector embeddings.
Supports upsert of embeddings and cosine similarity search.
"""
import json
import numpy as np
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..models.research import ResearchDoc
from ..schemas.research import (
    EmbeddingUpsertIn,
    SemanticQueryIn,
    SemanticQueryOut,
    SemanticHit,
)

router = APIRouter(prefix="/research", tags=["research/semantic"])


def _norm(v: np.ndarray) -> np.ndarray:
    """Normalize vector to unit length for cosine similarity"""
    n = np.linalg.norm(v)
    return v if n == 0 else v / n


@router.post("/embeddings/upsert")
def embeddings_upsert(
    payload: EmbeddingUpsertIn,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Store or update the embedding vector for a research document.
    Vector should be the same dimensionality across all docs.
    """
    doc = db.get(ResearchDoc, payload.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="doc not found")
    
    # Basic validation
    if not payload.vector or not isinstance(payload.vector, list):
        raise HTTPException(status_code=400, detail="vector required")
    
    if len(payload.vector) == 0:
        raise HTTPException(status_code=400, detail="vector cannot be empty")
    
    # Persist as JSON text
    doc.embedding_json = json.dumps(payload.vector, ensure_ascii=False)
    db.commit()
    
    return {
        "ok": True,
        "doc_id": doc.id,
        "dimension": len(payload.vector),
    }


@router.post("/semantic_query", response_model=SemanticQueryOut)
def semantic_query(
    payload: SemanticQueryIn,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Perform semantic search across research docs using cosine similarity.
    Requires a query vector with the same dimensionality as stored embeddings.
    Returns top_k most similar documents ranked by cosine score.
    """
    if not payload.vector:
        raise HTTPException(
            status_code=400,
            detail="vector is required for semantic search"
        )
    
    # Normalize query vector
    qv = _norm(np.array(payload.vector, dtype=float))
    
    # Fetch all docs with embeddings
    rows: List[ResearchDoc] = (
        db.query(ResearchDoc)
        .filter(ResearchDoc.embedding_json.isnot(None))
        .all()
    )
    
    hits: List[SemanticHit] = []
    
    for r in rows:
        try:
            # Parse stored embedding
            ev = np.array(json.loads(r.embedding_json), dtype=float)
            ev = _norm(ev)
            
            # Compute cosine similarity (dot product of normalized vectors)
            score = float(np.dot(qv, ev))
        except Exception as e:
            # Skip docs with invalid embeddings
            continue
        
        if score >= payload.min_score:
            # Create preview snippet from content
            preview = (r.content or "")[:220]
            
            hits.append(
                SemanticHit(
                    doc_id=r.id,
                    url=r.url or "",
                    title=r.title,
                    score=score,
                    preview=preview,
                )
            )
    
    # Sort by score descending and trim to top_k
    hits.sort(key=lambda h: h.score, reverse=True)
    top = hits[: max(1, min(payload.top_k, 50))]
    
    return SemanticQueryOut(hits=top)


@router.get("/embeddings/stats")
def embeddings_stats(
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Get statistics about stored embeddings.
    Returns count of docs with/without embeddings and sample dimensions.
    """
    total_docs = db.query(ResearchDoc).count()
    docs_with_embeddings = (
        db.query(ResearchDoc)
        .filter(ResearchDoc.embedding_json.isnot(None))
        .count()
    )
    
    # Get a sample embedding to check dimensionality
    sample = (
        db.query(ResearchDoc)
        .filter(ResearchDoc.embedding_json.isnot(None))
        .first()
    )
    
    sample_dimension = None
    if sample and sample.embedding_json:
        try:
            vec = json.loads(sample.embedding_json)
            sample_dimension = len(vec)
        except Exception:
            pass
    
    return {
        "total_docs": total_docs,
        "docs_with_embeddings": docs_with_embeddings,
        "docs_without_embeddings": total_docs - docs_with_embeddings,
        "coverage_pct": round(100 * docs_with_embeddings / total_docs, 1) if total_docs > 0 else 0,
        "sample_dimension": sample_dimension,
    }
