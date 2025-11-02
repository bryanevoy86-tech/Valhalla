"""
Background jobs for generating and updating embeddings on research documents.
"""

import json
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.core.embedding_utils import embed_text
from app.models.research import ResearchDoc


def embed_missing_docs(limit: int = 200) -> int:
    """
    Find docs without embeddings, generate & save vectors.
    
    Args:
        limit: Maximum number of docs to process in one run
    
    Returns:
        Count of documents that were embedded
    
    Usage:
        Typically called via /jobs/research/embed_missing endpoint
        or scheduled as a background task after ingestion.
    """
    db: Session = SessionLocal()
    try:
        # Query docs without embeddings
        rows = (
            db.query(ResearchDoc)
            .filter(ResearchDoc.embedding_json.is_(None))
            .order_by(ResearchDoc.id.asc())
            .limit(limit)
            .all()
        )
        
        count = 0
        for r in rows:
            # Generate embedding from document content
            # Use content field (or body_text if that's your field name)
            text_content = getattr(r, 'content', None) or getattr(r, 'body_text', '')
            vec = embed_text(text_content or "")
            
            # Store as JSON array
            r.embedding_json = json.dumps(vec, ensure_ascii=False)
            count += 1
        
        if count:
            db.commit()
        
        return count
    
    finally:
        db.close()
