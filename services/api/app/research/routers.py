from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .schemas import SearchQuery, SearchResponse, Source, UpsertPlaybook, Playbook
from .service import ResearchService
from .cache import TTLCache
from app.core.db import get_db
from .db_service import ResearchDB
import sqlalchemy as sa

router = APIRouter(prefix="/research", tags=["research"])
service = ResearchService()
cache = TTLCache(ttl_seconds=900, max_items=256)

@router.post("/search", response_model=SearchResponse)
def search(q: SearchQuery):
    key = f"q:{q.q}|limit:{q.limit}|tags:{q.tags}"
    cached = cache.get(key)
    if cached:
        return SearchResponse(query=q.q, results=cached, cached=True)
    results = service.search(q.q, q.limit, q.tags)
    cache.set(key, results)
    return SearchResponse(query=q.q, results=results, cached=False)

@router.get("/sources", response_model=list[Source])
def list_sources(db: Session = Depends(get_db)):
    return ResearchDB(db).list_sources()

@router.post("/sources", response_model=None)
def add_source(src: Source, db: Session = Depends(get_db)):
    ResearchDB(db).add_source(src)

@router.put("/playbooks/{key}", response_model=Playbook)
def upsert_playbook(key: str, body: UpsertPlaybook, db: Session = Depends(get_db)):
    return ResearchDB(db).upsert_playbook(key, body)

@router.get("/playbooks/{key}", response_model=Playbook)
def get_playbook(key: str, db: Session = Depends(get_db)):
    pb = ResearchDB(db).get_playbook(key)
    if not pb:
        raise HTTPException(status_code=404, detail="not found")
    return pb

@router.get("/playbooks", response_model=list[Playbook])
def list_playbooks(db: Session = Depends(get_db)):
    return ResearchDB(db).list_playbooks()


@router.get("/db-status")
def db_status(db: Session = Depends(get_db)):
    """Return alembic version and presence of research tables.
    Useful for post-deploy verification.
    """
    conn = db.get_bind()
    insp = sa.inspect(conn)
    tables = set(insp.get_table_names())
    try:
        version = conn.execute(sa.text("SELECT version_num FROM alembic_version"))
        row = version.first()
        alembic_version = row[0] if row else None
    except Exception:
        alembic_version = None
    return {
        "alembic_version": alembic_version,
        "tables": {
            "research_sources": "research_sources" in tables,
            "research_playbooks": "research_playbooks" in tables,
        },
    }
