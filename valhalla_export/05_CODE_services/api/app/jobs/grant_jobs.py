"""
Grant refresh jobs - stub for future API/scraping integration.
"""

from sqlalchemy.orm import Session
from ..core.db import SessionLocal
from ..models.grants import GrantSource, GrantRecord


def refresh_from_sources(limit: int = 50) -> int:
    """
    Stub: in future, fetch from APIs or scrape allowed feeds.
    For now, returns 0 so the job path exists.
    
    You can implement per-source handlers here (RSS, JSON, CSV).
    """
    # TODO: Implement source-specific refresh logic
    # Example:
    # db = SessionLocal()
    # try:
    #     sources = db.query(GrantSource).filter(GrantSource.active.is_(True)).limit(limit).all()
    #     for source in sources:
    #         # Fetch from source.url, parse, create GrantRecord instances
    #         pass
    #     return len(sources)
    # finally:
    #     db.close()
    
    return 0
