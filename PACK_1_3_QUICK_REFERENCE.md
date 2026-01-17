# PACK 1-3 QUICK REFERENCE GUIDE

## API Endpoints Summary

### P-DOCS-1: Document Vault
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/core/docs` | POST | Create document |
| `/core/docs` | GET | List documents |
| `/core/docs/{doc_id}` | GET | Get document |
| `/core/docs/{doc_id}` | PATCH | Update document |
| `/core/docs/bundle` | POST | Create bundle |

### P-KNOW-1: Knowledge Ingestion
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/core/knowledge_ingest/inbox` | POST | Create inbox item |
| `/core/knowledge_ingest/inbox` | GET | List inbox items |
| `/core/knowledge_ingest/inbox/{item_id}` | GET | Get item |
| `/core/knowledge_ingest/process` | POST | Process item (clean/chunk/index) |
| `/core/knowledge_ingest/search` | POST | Search content |

### P-COMMS-1: Communications Hub
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/core/comms` | POST | Create message |
| `/core/comms` | GET | List messages |
| `/core/comms/{msg_id}` | GET | Get message |
| `/core/comms/{msg_id}` | PATCH | Update message |
| `/core/comms/{msg_id}/mark_sent` | POST | Mark as sent |

---

## UUID Prefixes

| System | Type | Prefix | Example |
|--------|------|--------|---------|
| Docs | Document | `dc_` | dc_6b9512985f34 |
| Docs | Bundle | `bd_` | bd_7b2e20c29129 |
| Knowledge | Inbox item | `ki_` | ki_1034254ef3a3 |
| Knowledge | Chunk | `kc_` | kc_a1b2c3d4e5f6 |
| Comms | Message | `cm_` | cm_eb8597abf874 |

---

## Data Locations

**Documents**:
- `/backend/data/docs/docs.json` — Document records
- `/backend/data/docs/bundles.json` — Bundle manifests

**Knowledge**:
- `/backend/data/knowledge_ingest/inbox.json` — Inbox items
- `/backend/data/knowledge_ingest/chunks.json` — Text chunks
- `/backend/data/knowledge_ingest/index.json` — Keyword index

**Communications**:
- `/backend/data/comms/messages.json` — Message records

---

## Payload Examples

### P-DOCS-1: Create Document
```json
{
  "title": "Lease Agreement",
  "doc_type": "contract",
  "visibility": "internal",
  "file_path": "/docs/lease_2024.pdf",
  "mime": "application/pdf",
  "sha256": "abc123...",
  "tags": ["lease", "property"],
  "links": {"property": "pi_abc123"},
  "notes": "Main lease document",
  "meta": {"version": "2024-01"}
}
```

### P-DOCS-1: Create Bundle
```json
{
  "name": "Property Bundle Q1",
  "doc_ids": ["dc_abc", "dc_def"],
  "include_links": true,
  "include_notes": true,
  "meta": {"purpose": "sharing"}
}
```

### P-KNOW-1: Create Inbox Item
```json
{
  "title": "Funding Research Notes",
  "source_type": "note",
  "raw_text": "Researching SBA grants and business credit...",
  "tags": ["funding", "research"],
  "meta": {"priority": "high"}
}
```

### P-KNOW-1: Process Item
```json
{
  "item_id": "ki_abc",
  "action": "all",
  "max_chunk_chars": 900,
  "overlap_chars": 120
}
```

### P-KNOW-1: Search
```json
{
  "query": "business credit grants",
  "top_k": 5,
  "item_id": "",
  "tag": "funding"
}
```

### P-COMMS-1: Create Message
```json
{
  "title": "Buyer Introduction",
  "channel": "email",
  "status": "draft",
  "tone": "warm",
  "to": "buyer@example.com",
  "subject": "Off-Market Opportunity",
  "body": "Hi there, I have an interesting deal...",
  "deal_id": "dl_123",
  "contact_id": "",
  "partner_id": "",
  "tags": ["buyer", "deal"],
  "meta": {"source": "manual"}
}
```

### P-COMMS-1: Mark Sent
```json
{
  "sent_at": "2026-01-03T04:04:07Z",
  "meta": {"delivery_status": "delivered"}
}
```

---

## Filter Parameters

### P-DOCS-1: List Documents
```
?doc_type=contract
&visibility=internal
&tag=lease
&entity_type=property
&entity_id=pi_abc123
```

### P-KNOW-1: List Inbox
```
?stage=indexed
&tag=funding
```

### P-KNOW-1: Search
```json
{
  "query": "business credit",
  "top_k": 8,
  "item_id": "ki_abc",
  "tag": "funding"
}
```

### P-COMMS-1: List Messages
```
?status=draft
&channel=email
&deal_id=dl_123
```

---

## Enums

### DocType (P-DOCS-1)
- receipt, contract, id, invoice, statement, photo, note, other

### Visibility (P-DOCS-1)
- internal, shareable, private

### Stage (P-KNOW-1)
- inbox, cleaned, chunked, indexed

### Channel (P-COMMS-1)
- sms, email, call, dm, letter, other

### Status (P-COMMS-1)
- draft, queued, sent, canceled

### Tone (P-COMMS-1)
- neutral, warm, firm, urgent

---

## Common Patterns

### Document Linking
Documents can be linked to multiple entity types:
```python
links = {
  "property": "pi_abc123",
  "deal": "dl_def456",
  "partner": "pt_ghi789"
}
```

### Knowledge Pipeline
```
Create Item → Clean → Chunk → Index → Search
```

All steps can be done together with `action: "all"` or individually.

### Message Lifecycle
```
draft → queued → sent
                ↘ canceled
```

---

## Testing

**Run all tests**:
```bash
python test_pack_docs_knowledge_comms_unit.py
```

**Expected output**:
```
P-DOCS-1 (Document Vault):       PASS
P-KNOW-1 (Knowledge Ingestion):  PASS
P-COMMS-1 (Communications):      PASS

Overall: ALL SYSTEMS OPERATIONAL ✓
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Invalid input (missing required field, bad format) |
| 404 | Resource not found |
| 500 | Server error |

---

## Module Imports

```python
# For direct service access (testing):
from backend.app.core_gov.docs import service as docs_service
from backend.app.core_gov.knowledge_ingest import service as ki_service
from backend.app.core_gov.comms import service as comms_service

# For router integration:
from backend.app.core_gov.docs import docs_router
from backend.app.core_gov.knowledge_ingest import knowledge_ingest_router
from backend.app.core_gov.comms import comms_router
```

---

## Production Readiness Checklist

- ✅ All 3 systems deployed
- ✅ 15/15 tests passing
- ✅ Routers wired to core_router.py
- ✅ Data persistence working
- ✅ Error handling in place
- ✅ Documentation complete
- ✅ Ready for integration testing

---

## Troubleshooting

**Issue**: Tests failing with import errors
**Solution**: Ensure backend/app/core_gov/ directory structure exists and __init__.py files are in place

**Issue**: Data files not being created
**Solution**: Verify backend/data/{docs,knowledge_ingest,comms}/ directories exist and are writable

**Issue**: Search returns no results
**Solution**: 
1. Ensure item is fully processed (stage: "indexed")
2. Use queries with words that appear in the text
3. Check that stop words aren't filtering out your query

---

**For detailed API documentation**: See PACK_1_3_DEPLOYMENT_COMPLETE.md
