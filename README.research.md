# Pack 8: Research Agent & Playbooks

**Purpose**  
Lightweight in-memory research module with TTL cache, source registry, and playbook CRUD. Enables fast context-aware lookups and structured workflows ("playbooks").

## Features
- **TTL Cache** (`app/research/cache.py`): 900s default TTL, LRU eviction at max_items.
- **Research Service** (`app/research/service.py`): In-memory source list with default seed sources (Render Docs, FastAPI Docs). Pluggable fetcher (stub returns sources matching tags).
- **Schemas** (`app/research/schemas.py`): `Source`, `SearchQuery`, `Result`, `SearchResponse`, `Playbook`, `UpsertPlaybook`.
- **Routers** (`app/research/routers.py`):
  - `POST /api/research/search` → cached search (query + tags + limit).
  - `GET /api/research/sources` → list all sources.
  - `POST /api/research/sources` → add a source (dupe prevention by URL).
  - `PUT /api/research/playbooks/{key}` → upsert a playbook.
  - `GET /api/research/playbooks/{key}` → get playbook by key.
  - `GET /api/research/playbooks` → list all playbooks.
- **Re-export**: `app/routers/research.py` now imports and re-exports `app.research.routers.router`, integrating seamlessly with `main.py`.

## Current Integration
See `main_includes_research.patch` for how `main.py` loads this router (via `from app.routers.research import router as research_router` + safe availability check).

## Testing
- `tests/test_research_unit.py`: TTL cache roundtrip, expiry, eviction; service search/add; schema validation.
- `tests/test_research_router_import.py`: Confirms router loads with correct prefix/tags.
- All tests marked `@pytest.mark.unit` for CI coverage gate.

## Usage
```python
# Add a custom source
POST /api/research/sources
{
  "name": "Company Handbook",
  "url": "https://docs.example.com",
  "type": "doc",
  "tags": ["internal"]
}

# Search
POST /api/research/search
{
  "q": "render deployment",
  "limit": 5,
  "tags": ["deploy"]
}

# Upsert a playbook
PUT /api/research/playbooks/onboard_vendor
{
  "title": "Vendor Onboarding",
  "steps": ["Verify EIN", "Background check", "Sign MSA"],
  "tags": ["vendor", "compliance"]
}

# Get playbook
GET /api/research/playbooks/onboard_vendor
```

## DB Persistence (Pack 8.1)
- Tables: `research_sources` (adds `tags` column if missing), `research_playbooks` (new).
- Router now uses DB via `ResearchDB` service for sources and playbooks (search stays cached/in-memory for now).
- Migration: `services/api/alembic/versions/20251105_v3_9_research_db.py` (runs automatically on deploy via `alembic upgrade head`).

## Next Steps
- Swap in real fetcher (e.g., scrape/parse docs, call external APIs).
- Add semantic/vector search for richer matching.
- Expose metrics (cache hit rate, search latency).
