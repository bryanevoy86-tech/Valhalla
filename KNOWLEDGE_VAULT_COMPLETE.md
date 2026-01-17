## Knowledge Vault v1-4 (KV-1 through KV-4) — Complete Implementation

**Status:** ✅ COMPLETE  
**Date:** 2026-01-01  
**Components:** 4 (Register, Search, Linking, Step-Aware Retrieval)  

---

## Overview

Knowledge Vault provides a **file-backed knowledge management system** for Valhalla:
- **Store** known truth documents in `data/knowledge/clean/`
- **Track** them in `manifest.json` with metadata
- **Search** by keyword + filters
- **Link** docs to engines and GO steps
- **Retrieve** contextual docs for each GO step

---

## KV-1 — Register + List + Manifest

**Purpose:** Basic knowledge registry with file validation.

### Files Created (4)

1. `backend/app/core_gov/knowledge/__init__.py` (docstring)
2. `backend/app/core_gov/knowledge/models.py` (Pydantic models)
3. `backend/app/core_gov/knowledge/store.py` (file I/O + manifest management)
4. `backend/app/core_gov/knowledge/router.py` (endpoints)

### Data Directories Created (2)

- `data/knowledge/clean/` — Authoritative knowledge files
- `data/knowledge/inbox_raw/` — Raw input queue

### Endpoints (2)

#### `POST /core/knowledge/register`
Register a knowledge document (file must exist in `data/knowledge/clean/`).

**Request:**
```json
{
  "title": "Wholesale Deal Rules",
  "file_name": "test_rules.md",
  "tags": ["canon", "wholesale"],
  "source": "internal",
  "scope": "Wholesale deals",
  "truth_level": "decision",
  "version": "v1",
  "notes": "Core rules for wholesaling"
}
```

**Response:**
```json
{
  "title": "Wholesale Deal Rules",
  "file_name": "test_rules.md",
  "tags": ["canon", "wholesale"],
  "source": "internal",
  "scope": "Wholesale deals",
  "truth_level": "decision",
  "version": "v1",
  "notes": "Core rules for wholesaling",
  "id": "uuid-here",
  "created_at_utc": "2026-01-01T10:00:00.000Z"
}
```

**Validation:**
- File must exist in `data/knowledge/clean/`
- Audit log: `KNOWLEDGE_REGISTERED` event

#### `GET /core/knowledge/list?limit=200`
List all registered documents (newest first).

**Response:**
```json
{
  "items": [
    {
      "id": "uuid-1",
      "title": "Wholesale Deal Rules",
      "file_name": "test_rules.md",
      "tags": ["canon", "wholesale"],
      "created_at_utc": "2026-01-01T10:00:00Z",
      ...
    }
  ]
}
```

### Store Details

**manifest.json structure:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "...",
      "file_name": "...",
      "tags": [...],
      "source": "...",
      "truth_level": "decision|spec|draft|idea",
      "version": "v1",
      "created_at_utc": "...",
      "notes": "...",
      "meta": {}
    }
  ]
}
```

**Capacity:** 5000 documents (auto-capped, oldest removed)

---

## KV-2 — Search v1 (Keyword + Filters)

**Purpose:** Full-text search across knowledge documents.

### Files Created (1)

- `backend/app/core_gov/knowledge/search.py` (search logic)

### Endpoint (1)

#### `GET /core/knowledge/search?q=...&tag=...&limit=10`

Search documents by keyword + filter by tags.

**Query Parameters:**
- `q` (str, optional): Keyword to search in title, tags, and file content
- `tag` (str, optional): Filter by tag (case-insensitive)
- `limit` (int, default=10): Max results to return

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Wholesale Deal Rules",
      "file_name": "test_rules.md",
      "tags": ["canon", "wholesale"],
      "truth_level": "decision",
      "version": "v1",
      "source": "internal",
      "snippet": "...Always verify title is clean. Do not accept fractional..."
    }
  ]
}
```

**Search Behavior:**
- Searches in: title + tags + file content (first 50K chars)
- Returns: Snippets with context window around keyword
- File support: `.md`, `.txt` only
- Manifest-based (not raw folder scan)

### Example Searches

```bash
# Search for "rules" keyword
curl "http://localhost:4000/core/knowledge/search?q=rules&limit=5"

# Filter by tag "canon"
curl "http://localhost:4000/core/knowledge/search?tag=canon&limit=5"

# Combine: search "capital" with "canon" tag
curl "http://localhost:4000/core/knowledge/search?q=capital&tag=canon&limit=5"
```

---

## KV-3 — Linking (Tie Docs to Engines + GO Steps)

**Purpose:** Cross-reference docs to business engines and workflow steps.

### Files Created (2)

- `backend/app/core_gov/knowledge/link_models.py` (LinkRequest model)
- `backend/app/core_gov/knowledge/link_store.py` (link persistence)

### Endpoints (3)

#### `POST /core/knowledge/link`
Link a document to engine(s) and/or GO step(s).

**Request:**
```json
{
  "doc_id": "uuid-from-list",
  "engine": "wholesaling",
  "step_id": "intake_ready",
  "tags": []
}
```

**Validation:**
- At least one of `engine` or `step_id` must be provided
- Audit log: `KNOWLEDGE_LINKED` event

**Response:**
```json
{"ok": true}
```

#### `GET /core/knowledge/for_engine?engine=wholesaling`
Get all documents linked to an engine.

**Response:**
```json
{
  "engine": "wholesaling",
  "items": [
    {
      "id": "uuid",
      "title": "Wholesale Deal Rules",
      "file_name": "test_rules.md",
      "tags": ["canon"],
      "truth_level": "decision",
      "version": "v1",
      "source": "internal"
    }
  ]
}
```

#### `GET /core/knowledge/for_step?step_id=intake_ready`
Get all documents linked to a GO step.

**Response:**
```json
{
  "step_id": "intake_ready",
  "items": [
    {
      "id": "uuid",
      "title": "Wholesale Deal Rules",
      ...
    }
  ]
}
```

### Link Storage

**links.json structure:**
```json
{
  "by_engine": {
    "wholesaling": ["doc_id_1", "doc_id_2"],
    "fix_flip": ["doc_id_3"]
  },
  "by_step": {
    "intake_ready": ["doc_id_1"],
    "capital_check": ["doc_id_2"]
  }
}
```

---

## KV-4 — Step-Aware Retrieval (Next Step + Sources)

**Purpose:** Provide contextual knowledge for the current GO step.

### Files Created (1)

- `backend/app/core_gov/go/sources_service.py` (service logic)

### Endpoint (1)

#### `GET /core/go/next_step_with_sources`
Get next GO step WITH linked documents and search suggestions.

**Response:**
```json
{
  "next": {
    "next_step": {
      "id": "intake_ready",
      "title": "Intake: Verify customer record",
      "description": "...",
      ...
    },
    "session_id": "go_20260101_100000",
    "status": "IN_PROGRESS",
    "current_step": 3,
    ...
  },
  "sources": [
    {
      "id": "uuid",
      "title": "Wholesale Deal Rules",
      "file_name": "test_rules.md",
      "tags": ["canon"],
      "truth_level": "decision",
      "version": "v1",
      "source": "internal"
    }
  ],
  "suggestions": [
    {
      "id": "uuid",
      "title": "Customer Verification Checklist",
      "file_name": "customer_checklist.md",
      "snippet": "..."
    }
  ]
}
```

**Components:**
1. **next:** Full GO next_step response (existing behavior)
2. **sources:** Documents explicitly linked to this step
3. **suggestions:** Light keyword search based on step title

### Use Case

**For GO Mode Integration:**
```python
# Instead of just next_step(), get step WITH docs
resp = httpx.get("http://localhost:4000/core/go/next_step_with_sources")
step_data = resp.json()

# Operator sees:
# 1. What to do: step_data["next"]["next_step"]["title"]
# 2. Why: step_data["sources"] (linked docs)
# 3. Hints: step_data["suggestions"] (keyword matches)
```

---

## Integration Points

### core_router.py Changes

**Imports Added:**
```python
from .knowledge.router import router as knowledge_router
from .go.sources_service import next_step_with_sources
```

**Router Include:**
```python
core.include_router(knowledge_router)
```

**Endpoint Added:**
```python
@core.get("/go/next_step_with_sources")
def go_next_step_with_sources():
    return next_step_with_sources()
```

**Lines Modified:** 4 total (2 imports, 1 include, 1 endpoint definition)

---

## Complete Endpoint Map

| PACK | Endpoint | Method | Purpose |
|------|----------|--------|---------|
| KV-1 | /core/knowledge/register | POST | Register document |
| KV-1 | /core/knowledge/list | GET | List documents |
| KV-2 | /core/knowledge/search | GET | Search by keyword/tag |
| KV-3 | /core/knowledge/link | POST | Link doc to engine/step |
| KV-3 | /core/knowledge/for_engine | GET | Get docs for engine |
| KV-3 | /core/knowledge/for_step | GET | Get docs for step |
| KV-4 | /core/go/next_step_with_sources | GET | Next step with docs |

**Total New Endpoints:** 7

---

## File Inventory

### Code Files (8)

```
backend/app/core_gov/knowledge/
  ├── __init__.py                (1 line)   - Package docstring
  ├── models.py                  (~20 lines) - KnowledgeDocIn, KnowledgeDoc
  ├── store.py                   (~55 lines) - Manifest load/save, doc registration
  ├── router.py                  (~55 lines) - All 7 endpoints
  ├── search.py                  (~85 lines) - Full-text search with snippets
  ├── link_models.py             (10 lines)  - LinkRequest model
  └── link_store.py              (~40 lines) - Link persistence

backend/app/core_gov/go/
  └── sources_service.py         (~45 lines) - Step-aware doc retrieval
```

### Data Files (1)

```
data/knowledge/
  ├── clean/
  │   └── test_rules.md          (Test document for verification)
  └── inbox_raw/                 (Empty inbox for future imports)
```

### Manifest/Links Files (Created at Runtime)

```
data/knowledge/
  ├── manifest.json              (Doc registry)
  └── links.json                 (Doc-to-engine/step mappings)
```

---

## Test Workflow

### Step 1: List Documents
```bash
curl http://localhost:4000/core/knowledge/list?limit=5
# Initially empty, returns {"items": []}
```

### Step 2: Register Document
```bash
curl -X POST http://localhost:4000/core/knowledge/register \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Rules",
    "file_name": "test_rules.md",
    "tags": ["canon"],
    "source": "internal",
    "truth_level": "draft",
    "version": "v1"
  }'
```

**Expected:** Returns doc with ID and created_at_utc

### Step 3: List Again
```bash
curl http://localhost:4000/core/knowledge/list?limit=5
# Now shows registered doc
```

### Step 4: Search
```bash
curl "http://localhost:4000/core/knowledge/search?q=rules&limit=5"
# Returns snippet showing keyword context
```

### Step 5: Link to Engine
First, get the doc_id from list or register response.

```bash
curl -X POST http://localhost:4000/core/knowledge/link \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "<PASTE_DOC_ID>",
    "engine": "wholesaling",
    "step_id": "intake_ready"
  }'
```

### Step 6: Retrieve for Engine
```bash
curl "http://localhost:4000/core/knowledge/for_engine?engine=wholesaling"
# Returns all docs linked to wholesaling
```

### Step 7: Retrieve for Step
```bash
curl "http://localhost:4000/core/knowledge/for_step?step_id=intake_ready"
# Returns all docs linked to intake_ready step
```

### Step 8: Get Next Step with Sources
```bash
curl http://localhost:4000/core/go/next_step_with_sources
# Returns next GO step + linked docs + search suggestions
```

---

## Design Decisions

1. **File-Backed Manifest:** Registry stored in JSON (not database) to keep governance data portable

2. **Supported Formats:** `.md` and `.txt` only (safe text formats, easy to parse)

3. **Manifest Index:** Search uses manifest to find files (not raw directory scan) to maintain control

4. **Graceful Missing Files:** Search returns empty if file doesn't exist (handles deletion)

5. **Link De-duplication:** Same doc_id won't be added twice to engine/step lists

6. **Manifest Capping:** Auto-removes oldest docs if >5000 (prevents unbounded growth)

7. **Snippet Context:** Search snippets show keyword with surrounding text (140 char window)

8. **Step Suggestions:** Light keyword search on step title (no heavy NLP, just substring match)

---

## Integration with GO Mode

**Without KV-4:**
```
GET /core/go/next_step
→ Operator sees step ID + title
→ Must manually search docs
```

**With KV-4:**
```
GET /core/go/next_step_with_sources
→ Operator sees step + linked docs + suggestions
→ Docs right there for reference
→ All in one call
```

---

## Capacity & Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Max docs in manifest | 5000 | Auto-capped, oldest removed |
| Max file size | 200KB | Per-file read limit for search |
| Search haystack | First 50KB | Title + tags + content prefix |
| Snippet window | 140 chars | Around keyword match |
| Links per doc | Unlimited | No hard cap on engine/step pairs |

---

## Error Handling

**Register Endpoint:**
- 400 if file not found in `data/knowledge/clean/`

**Link Endpoint:**
- 400 if neither `engine` nor `step_id` provided

**Search Endpoint:**
- Returns empty list if no matches (not error)

**File Ops:**
- Text read errors ignored (UTF-8 fallback + error tolerance)
- Missing manifest returns empty list (not error)

---

## Summary

**Knowledge Vault v1-4 provides:**
✅ Centralized knowledge registry (KV-1)
✅ Full-text search (KV-2)
✅ Cross-referencing to engines/steps (KV-3)
✅ Contextual retrieval for GO steps (KV-4)

**Total code:** ~350 lines across 8 Python files + 1 test markdown file
**Total endpoints:** 7
**Data directories:** 2 (clean, inbox_raw)
**Integration:** 1 router include + 1 endpoint in core_router.py

**Ready for:** Immediate testing and integration with GO Mode dashboards.

