import re
import requests
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup

from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..models.research import ResearchSource, ResearchDoc, ResearchQuery
from ..schemas.research import (
    SourceIn, SourceOut, IngestIn, IngestOut, QueryIn, QueryOut, QueryResult
)

router = APIRouter(prefix="/research", tags=["research"])


@router.get("/keys")
def get_keys(_: bool = Depends(require_builder_key)):
    """Debug endpoint to confirm API key is working"""
    return {"ok": True, "message": "Research API key validated"}


@router.get("/sources", response_model=List[SourceOut])
def list_sources(db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """List all research sources"""
    sources = db.query(ResearchSource).order_by(ResearchSource.id.desc()).all()
    return sources


@router.post("/sources", response_model=SourceOut)
def create_source(payload: SourceIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """Add a new research source"""
    source = ResearchSource(
        name=payload.name,
        url=payload.url,
        kind=payload.kind,
        ttl_seconds=payload.ttl_seconds,
        enabled=payload.enabled,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.post("/ingest", response_model=IngestOut)
def ingest_source(payload: IngestIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """Fetch and ingest content from a source"""
    source = db.get(ResearchSource, payload.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    if not source.enabled:
        raise HTTPException(status_code=400, detail="Source is disabled")

    # Fetch content
    try:
        response = requests.get(source.url, timeout=30, headers={"User-Agent": "Heimdall-ResearchBot/1.0"})
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch URL: {str(e)}")

    # Parse HTML and extract text
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        # Remove script and style elements
        for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
            script_or_style.decompose()
        
        # Get text
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Get title
        title = soup.title.string if soup.title else source.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse content: {str(e)}")

    # Clear old docs for this source
    db.query(ResearchDoc).filter(ResearchDoc.source_id == source.id).delete()

    # Store the document (simple version - single doc, can split into chunks later)
    doc = ResearchDoc(
        source_id=source.id,
        title=title,
        url=source.url,
        content=text[:500000],  # Limit to 500KB of text
        chunk_index=0,
        ingested_at=datetime.utcnow(),
    )
    db.add(doc)
    
    # Update source
    source.last_ingested_at = datetime.utcnow()
    db.add(source)
    db.commit()

    return IngestOut(
        ok=True,
        source_id=source.id,
        doc_count=1,
        message=f"Ingested {len(text)} characters from {source.name}"
    )


@router.post("/query", response_model=QueryOut)
def query_docs(payload: QueryIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """Search ingested documents for relevant content"""
    query_text = payload.q.lower()
    
    # Simple keyword search (can upgrade to FTS or vector search later)
    docs = db.query(ResearchDoc).join(ResearchSource).filter(
        ResearchSource.enabled == True
    ).all()
    
    results = []
    for doc in docs:
        content_lower = doc.content.lower()
        if query_text in content_lower:
            # Find snippet around match
            match_pos = content_lower.find(query_text)
            start = max(0, match_pos - 100)
            end = min(len(doc.content), match_pos + len(query_text) + 100)
            snippet = doc.content[start:end].strip()
            
            # Simple relevance: count occurrences
            relevance = content_lower.count(query_text)
            
            results.append(QueryResult(
                source_name=doc.source.name,
                doc_id=doc.id,
                title=doc.title,
                url=doc.url,
                snippet=f"...{snippet}...",
                relevance_score=float(relevance)
            ))
    
    # Sort by relevance
    results.sort(key=lambda x: x.relevance_score, reverse=True)
    results = results[:payload.limit]
    
    # Log the query
    query_log = ResearchQuery(
        query_text=payload.q,
        result_count=len(results),
        created_at=datetime.utcnow(),
    )
    db.add(query_log)
    db.commit()
    
    return QueryOut(
        query=payload.q,
        result_count=len(results),
        results=results
    )
