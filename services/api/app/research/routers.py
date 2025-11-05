from fastapi import APIRouter, HTTPException
from typing import Dict
from .schemas import SearchQuery, SearchResponse, Source, UpsertPlaybook, Playbook
from .service import ResearchService
from .cache import TTLCache

router = APIRouter(prefix="/research", tags=["research"])
service = ResearchService()
cache = TTLCache(ttl_seconds=900, max_items=256)

# In-memory playbooks (swap to DB later)
_PLAYBOOKS: Dict[str, Playbook] = {}

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
def list_sources():
    return service.list_sources()

@router.post("/sources", response_model=None)
def add_source(src: Source):
    service.add_source(src)

@router.put("/playbooks/{key}", response_model=Playbook)
def upsert_playbook(key: str, body: UpsertPlaybook):
    pb = Playbook(key=key, **body.model_dump())
    _PLAYBOOKS[key] = pb
    return pb

@router.get("/playbooks/{key}", response_model=Playbook)
def get_playbook(key: str):
    pb = _PLAYBOOKS.get(key)
    if not pb:
        raise HTTPException(status_code=404, detail="not found")
    return pb

@router.get("/playbooks", response_model=list[Playbook])
def list_playbooks():
    return list(_PLAYBOOKS.values())
