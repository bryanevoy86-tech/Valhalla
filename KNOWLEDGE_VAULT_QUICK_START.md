## Knowledge Vault — Quick Start & curl Examples

### KV-1: Register & List

**Create a test file first:**
```bash
# File already exists at: data/knowledge/clean/test_rules.md
```

**Register it:**
```bash
curl -X POST http://localhost:4000/core/knowledge/register \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Rules",
    "file_name": "test_rules.md",
    "tags": ["canon", "wholesale"],
    "source": "internal",
    "truth_level": "draft",
    "version": "v1"
  }'
```

**List all docs:**
```bash
curl http://localhost:4000/core/knowledge/list?limit=5
```

### KV-2: Search

**Search by keyword:**
```bash
curl "http://localhost:4000/core/knowledge/search?q=rules&limit=5"
curl "http://localhost:4000/core/knowledge/search?q=capital&limit=5"
```

**Filter by tag:**
```bash
curl "http://localhost:4000/core/knowledge/search?tag=canon&limit=5"
```

**Combined (keyword + tag):**
```bash
curl "http://localhost:4000/core/knowledge/search?q=verify&tag=canon&limit=10"
```

### KV-3: Linking

**Get doc_id from list response, then link:**
```bash
# First, list to get a doc_id
curl http://localhost:4000/core/knowledge/list | jq '.items[0].id'

# Link that doc to engine + step
DOC_ID="<paste-id-here>"
curl -X POST http://localhost:4000/core/knowledge/link \
  -H "Content-Type: application/json" \
  -d "{
    \"doc_id\": \"$DOC_ID\",
    \"engine\": \"wholesaling\",
    \"step_id\": \"intake_ready\"
  }"
```

**Get docs for engine:**
```bash
curl "http://localhost:4000/core/knowledge/for_engine?engine=wholesaling"
```

**Get docs for GO step:**
```bash
curl "http://localhost:4000/core/knowledge/for_step?step_id=intake_ready"
```

### KV-4: Step-Aware Retrieval

**Get next step WITH documents:**
```bash
curl http://localhost:4000/core/go/next_step_with_sources
```

**Parse response:**
```bash
curl http://localhost:4000/core/go/next_step_with_sources | jq '.next.next_step.title'
curl http://localhost:4000/core/go/next_step_with_sources | jq '.sources'
curl http://localhost:4000/core/go/next_step_with_sources | jq '.suggestions'
```

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /core/knowledge/register | POST | Register doc |
| /core/knowledge/list | GET | List docs |
| /core/knowledge/search | GET | Search docs |
| /core/knowledge/link | POST | Link doc→engine/step |
| /core/knowledge/for_engine | GET | Get docs for engine |
| /core/knowledge/for_step | GET | Get docs for step |
| /core/go/next_step_with_sources | GET | Next step + docs |

---

## Files Created

**Code (8 files):**
- backend/app/core_gov/knowledge/__init__.py
- backend/app/core_gov/knowledge/models.py
- backend/app/core_gov/knowledge/store.py
- backend/app/core_gov/knowledge/router.py
- backend/app/core_gov/knowledge/search.py
- backend/app/core_gov/knowledge/link_models.py
- backend/app/core_gov/knowledge/link_store.py
- backend/app/core_gov/go/sources_service.py

**Data (3):**
- data/knowledge/clean/test_rules.md (test file)
- data/knowledge/clean/ (directory)
- data/knowledge/inbox_raw/ (directory)

**Generated at Runtime:**
- data/knowledge/manifest.json (doc registry)
- data/knowledge/links.json (cross-references)

---

## Testing Sequence

1. **Register** → POST /core/knowledge/register
2. **List** → GET /core/knowledge/list
3. **Search** → GET /core/knowledge/search?q=...
4. **Link** → POST /core/knowledge/link
5. **Retrieve for Engine** → GET /core/knowledge/for_engine
6. **Retrieve for Step** → GET /core/knowledge/for_step
7. **Step with Sources** → GET /core/go/next_step_with_sources

---

## Document Metadata

```json
{
  "id": "uuid",
  "title": "Document title",
  "file_name": "document.md",
  "tags": ["tag1", "tag2"],
  "source": "internal|notes|logs|etc",
  "scope": "What it covers",
  "truth_level": "decision|spec|draft|idea",
  "version": "v1",
  "notes": "Optional notes",
  "created_at_utc": "ISO timestamp",
  "meta": {}
}
```

---

## Supported File Types

- `.md` (Markdown)
- `.txt` (Text)

Other formats (.pdf, .docx, .json) will be rejected.

---

## Limits

- **Max docs:** 5000 (auto-capped)
- **Max file size:** 200KB (per-file read limit)
- **Search haystack:** First 50KB (title + tags + content)
- **Results per query:** Configurable (default 10)

---

## Design Highlights

✅ File-backed (portable, no DB needed)
✅ Manifest-based (controlled indexing)
✅ Search with snippets (context window)
✅ Link to engines & GO steps
✅ Step-aware suggestions
✅ Graceful missing file handling
✅ Auto-capping to prevent unbounded growth

