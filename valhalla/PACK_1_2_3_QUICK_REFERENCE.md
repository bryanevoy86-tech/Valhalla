# PACK 1, 2, 3 Quick Reference Card

## 🚀 TL;DR

Three new modules deployed and live:
- **PACK 1:** Communication Hub (6 endpoints) - `/core/comms`
- **PACK 2:** Partner/JV Manager (8 endpoints) - `/core/jv`
- **PACK 3:** Property Intelligence (10 endpoints) - `/core/property`

**Status:** ✅ All working, tested, documented

---

## 📦 What's Installed

```
15 Python files (5 per module)
24 API endpoints
8 JSON data files (auto-created)
0 external dependencies (uses FastAPI, Pydantic - already in project)
```

---

## 🔌 Integration

Already wired into `backend/app/core_gov/core_router.py`:
```python
from .comms.router import router as comms_router
from .jv.router import router as jv_router
from .property.router import router as property_router

core.include_router(comms_router)
core.include_router(jv_router)
core.include_router(property_router)
```

---

## 📍 File Locations

**Code:**
```
backend/app/core_gov/comms/
backend/app/core_gov/jv/
backend/app/core_gov/property/
```

**Data:**
```
backend/data/comms/
backend/data/jv/
backend/data/property/
```

**Docs:**
```
PACK_1_2_3_IMPLEMENTATION.md
PACK_1_2_3_API_REFERENCE.md
PACK_1_2_3_CHECKLIST.md
DEPLOYMENT_REPORT_PACK_1_2_3.md
```

---

## 🧪 Testing

```bash
# Run comprehensive smoke tests
python backend/tests/smoke_packs_1_2_3.py

# Expected output:
# ✅ PACK 1 ALL TESTS PASSED
# ✅ PACK 2 ALL TESTS PASSED
# ✅ PACK 3 ALL TESTS PASSED
# 🎉 ALL PACKS VALIDATED SUCCESSFULLY!
```

---

## 📝 PACK 1 Cheat Sheet (Communications)

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Create draft | `/core/comms/drafts` | POST |
| List drafts | `/core/comms/drafts` | GET |
| Get draft | `/core/comms/drafts/{id}` | GET |
| Update draft | `/core/comms/drafts/{id}` | PATCH |
| Mark sent | `/core/comms/drafts/{id}/mark_sent` | POST |
| View log | `/core/comms/sendlog` | GET |

**Example:**
```bash
curl -X POST http://localhost:8000/core/comms/drafts \
  -H "Content-Type: application/json" \
  -d '{
    "body": "Hello there",
    "channel": "sms",
    "to": "+1234567890"
  }'
```

---

## 👥 PACK 2 Cheat Sheet (Partners/JV)

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Create partner | `/core/jv/partners` | POST |
| List partners | `/core/jv/partners` | GET |
| Get partner | `/core/jv/partners/{id}` | GET |
| Update partner | `/core/jv/partners/{id}` | PATCH |
| Create link | `/core/jv/links` | POST |
| List links | `/core/jv/links` | GET |
| Update link | `/core/jv/links/{id}` | PATCH |
| Dashboard | `/core/jv/partners/{id}/dashboard` | GET |

**Example:**
```bash
curl -X POST http://localhost:8000/core/jv/partners \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Development",
    "role": "jv_partner",
    "email": "contact@acme.com"
  }'
```

---

## 🏠 PACK 3 Cheat Sheet (Properties)

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Create property | `/core/property/properties` | POST |
| List properties | `/core/property/properties` | GET |
| Get property | `/core/property/properties/{id}` | GET |
| Update property | `/core/property/properties/{id}` | PATCH |
| Set rating | `/core/property/properties/{id}/neighborhood_rating` | POST |
| Get rating | `/core/property/properties/{id}/neighborhood_rating` | GET |
| Request comps | `/core/property/comps` | POST |
| Get comps | `/core/property/properties/{id}/comps` | GET |
| Set estimate | `/core/property/properties/{id}/repair_rent` | POST |
| Get estimate | `/core/property/properties/{id}/repair_rent` | GET |

**Example:**
```bash
curl -X POST http://localhost:8000/core/property/properties \
  -H "Content-Type: application/json" \
  -d '{
    "address": "123 Main St",
    "country": "CA",
    "region": "ON",
    "city": "Toronto"
  }'
```

---

## 🔍 Common Query Patterns

### Filter by Status
```bash
# Comms
GET /core/comms/drafts?status=draft
GET /core/comms/drafts?status=sent

# JV
GET /core/jv/partners?status=active
GET /core/jv/partners?status=paused

# Property
GET /core/property/properties?status=analyzing
```

### Filter by Related Resource
```bash
# Comms
GET /core/comms/drafts?deal_id=deal_001
GET /core/comms/sendlog?deal_id=deal_001

# JV
GET /core/jv/links?partner_id=p_xxxxx
GET /core/jv/links?deal_id=deal_001

# Property
GET /core/property/properties?country=CA&region=ON
```

---

## 💾 Data Model Quick Reference

### PACK 1 - Draft
```json
{
  "id": "dr_xxxxx",
  "channel": "sms|email|call|dm|letter|other",
  "body": "message",
  "status": "draft|ready|sent|archived",
  "to": "+1234567890",
  "subject": "for email",
  "deal_id": "deal_001",
  "contact_id": "contact_001",
  "tags": ["urgent"],
  "created_at": "2026-01-03T...",
  "updated_at": "2026-01-03T..."
}
```

### PACK 2 - Partner
```json
{
  "id": "p_xxxxx",
  "name": "Company Name",
  "role": "jv_partner|buyer|lender|gc|pm|agent|other",
  "status": "active|paused|archived",
  "email": "contact@company.com",
  "phone": "+1234567890",
  "tags": ["tier-1"],
  "created_at": "2026-01-03T...",
  "updated_at": "2026-01-03T..."
}
```

### PACK 3 - Property
```json
{
  "id": "pr_xxxxx",
  "address": "123 Main St",
  "country": "CA|US",
  "region": "ON",
  "city": "Toronto",
  "postal": "M5V 3A8",
  "status": "tracked|analyzing|offered|under_contract|sold|archived",
  "deal_id": "deal_001",
  "created_at": "2026-01-03T...",
  "updated_at": "2026-01-03T..."
}
```

---

## ⚡ Common Operations

### Create + Update Workflow
```bash
# 1. Create
ID=$(curl -X POST http://localhost:8000/core/comms/drafts \
  -H "Content-Type: application/json" \
  -d '{"body": "Test"}' | jq -r '.id')

# 2. Update
curl -X PATCH http://localhost:8000/core/comms/drafts/$ID \
  -H "Content-Type: application/json" \
  -d '{"status": "ready"}'

# 3. Send
curl -X POST http://localhost:8000/core/comms/drafts/$ID/mark_sent
```

### Partner + Link Workflow
```bash
# 1. Create partner
PARTNER_ID=$(curl -X POST http://localhost:8000/core/jv/partners \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme"}' | jq -r '.id')

# 2. Link to deal
curl -X POST http://localhost:8000/core/jv/links \
  -H "Content-Type: application/json" \
  -d "{\"partner_id\": \"$PARTNER_ID\", \"deal_id\": \"deal_001\"}"

# 3. View dashboard
curl http://localhost:8000/core/jv/partners/$PARTNER_ID/dashboard
```

---

## 🔧 Troubleshooting

### Module not found?
- Verify: `backend/app/core_gov/comms/`, `jv/`, `property/` exist
- Run: `python -c "from backend.app.core_gov.comms.router import router"`

### Data files not created?
- They auto-create on first API call
- Check: `ls backend/data/comms/drafts.json`

### 404 errors?
- Verify IDs are correct (prefix: `dr_`, `p_`, `pr_`, `lnk_`, etc.)
- Check endpoint path (case-sensitive)

### 400 validation errors?
- Required fields: `body` (comms), `name` (jv partner), `address` (property)
- Check field types match schema

---

## 📚 Full Documentation

See detailed docs in workspace root:
- `PACK_1_2_3_IMPLEMENTATION.md` - Architecture
- `PACK_1_2_3_API_REFERENCE.md` - All endpoints + examples
- `PACK_1_2_3_CHECKLIST.md` - Implementation details
- `DEPLOYMENT_REPORT_PACK_1_2_3.md` - Deployment status

---

## ✅ Status

| Component | Status | Tests |
|-----------|--------|-------|
| PACK 1 | ✅ Live | ✅ Pass |
| PACK 2 | ✅ Live | ✅ Pass |
| PACK 3 | ✅ Live | ✅ Pass |
| **Overall** | **✅ Ready** | **✅ All Green** |

**Ready for:** API calls, integration, staging deployment

---

**Last Updated:** January 2, 2026 | **System:** Valhalla v1
