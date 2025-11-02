"""
Research background jobs - automated ingestion and maintenance
"""
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.models.research import ResearchSource, ResearchDoc
from app.core.settings import settings


def get_session():
    """Create a new database session for background jobs"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def ingest_source(source: ResearchSource, db) -> dict:
    """
    Fetch and ingest content from a single source.
    Returns dict with status info.
    """
    try:
        # Fetch content
        response = requests.get(
            source.url, 
            timeout=30, 
            headers={"User-Agent": "Heimdall-ResearchBot/1.0"}
        )
        response.raise_for_status()

        # Parse HTML and extract text
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

        # Clear old docs for this source
        db.query(ResearchDoc).filter(ResearchDoc.source_id == source.id).delete()

        # Store the document
        doc = ResearchDoc(
            source_id=source.id,
            title=title,
            url=source.url,
            content=text[:500000],  # Limit to 500KB
            chunk_index=0,
            ingested_at=datetime.utcnow(),
        )
        db.add(doc)
        
        # Update source
        source.last_ingested_at = datetime.utcnow()
        db.add(source)
        db.commit()

        return {
            "ok": True,
            "source_id": source.id,
            "source_name": source.name,
            "chars": len(text),
            "message": f"Ingested {len(text)} chars"
        }

    except Exception as e:
        return {
            "ok": False,
            "source_id": source.id,
            "source_name": source.name,
            "error": str(e)
        }


def ingest_all_enabled() -> dict:
    """
    Ingest all enabled research sources.
    Designed to be called from a cron job or scheduled task.
    """
    db = get_session()
    try:
        sources = db.query(ResearchSource).filter(ResearchSource.enabled == True).all()
        
        results = []
        success_count = 0
        error_count = 0

        for source in sources:
            result = ingest_source(source, db)
            results.append(result)
            if result["ok"]:
                success_count += 1
            else:
                error_count += 1

        return {
            "ok": True,
            "job": "research.ingest_all",
            "timestamp": datetime.utcnow().isoformat(),
            "total_sources": len(sources),
            "success": success_count,
            "errors": error_count,
            "results": results
        }

    except Exception as e:
        return {
            "ok": False,
            "job": "research.ingest_all",
            "error": str(e)
        }
    finally:
        db.close()
