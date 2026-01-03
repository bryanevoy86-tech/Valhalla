# Deal Bank DB-6 & DB-7 — Import/Export + Pipeline Summary

**Status:** ✅ COMPLETE  
**Files Created:** 4 (2 for DB-6, 2 for DB-7)  
**Routers Wired:** 2  
**Endpoints:** 5 (4 import/export + 1 summary)  
**Total Deal Bank Now:** DB-0 through DB-7 (9 components, 13 endpoints)

---

## DB-6: Import/Export (CSV + JSON)

### Purpose
Enable bulk data import/export for deal pipeline. Forces `lead_source` (real|public|seed) so the system can't misclassify origins.

### Files Created

**[backend/app/core_gov/deals/import_export.py](backend/app/core_gov/deals/import_export.py)**
- `import_json(items, forced_source)` — Bulk JSON import with validation
- `import_csv_text(csv_text, forced_source)` — CSV text upload
- `export_json(limit)` — Export deals as JSON array
- `export_csv(limit)` — Export deals as CSV text
- Header mapping: Handles "country"/"Country", "state"/"State", "arv"/"ARV", etc.
- Type coercion: Floats, ints, tag lists (pipe or comma separated)
- Validation: Pydantic DealIn on every row

**[backend/app/core_gov/deals/import_export_router.py](backend/app/core_gov/deals/import_export_router.py)**
- `POST /core/deals/import/json` — Bulk JSON import
- `POST /core/deals/import/csv` — CSV text upload
- `GET /core/deals/export/json` — Export JSON (limit query param)
- `GET /core/deals/export/csv` — Export CSV (limit query param)

### Endpoints

#### Import JSON
```bash
curl -X POST http://localhost:4000/core/deals/import/json \
  -H "Content-Type: application/json" \
  -d '{
    "lead_source": "real",
    "items": [
      {
        "country": "CA",
        "province_state": "ON",
        "city": "Toronto",
        "strategy": "wholesale",
        "property_type": "sfh",
        "asking_price": 350000,
        "arv": 500000,
        "est_repairs": 40000,
        "seller_motivation": "high",
        "stage": "new"
      }
    ]
  }'
```

**Response:**
```json
{"created": 1, "errors": []}
```

#### Import CSV
```bash
curl -X POST http://localhost:4000/core/deals/import/csv \
  -H "Content-Type: application/json" \
  -d '{
    "lead_source": "public",
    "csv": "country,province_state,city,strategy,asking_price,arv,est_repairs,seller_motivation,stage\nCA,MB,Winnipeg,wholesale,200000,300000,25000,high,new\nUS,TX,Dallas,flip,180000,280000,30000,medium,new"
  }'
```

**Response:**
```json
{"created": 2, "errors": []}
```

#### Export JSON
```bash
curl "http://localhost:4000/core/deals/export/json?limit=100"
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid-1",
      "created_at_utc": "2026-01-01T12:00:00Z",
      "country": "CA",
      "province_state": "ON",
      "city": "Toronto",
      ...
    }
  ]
}
```

#### Export CSV
```bash
curl "http://localhost:4000/core/deals/export/csv?limit=100"
```

**Response:**
```
id,created_at_utc,updated_at_utc,country,province_state,city,strategy,...
uuid-1,2026-01-01T12:00:00Z,2026-01-01T12:00:00Z,CA,ON,Toronto,wholesale,...
```

### Features

**Header Flexibility:**
- Accepts: "country" or "Country"
- Accepts: "state" / "State" / "province" / "Province"
- Accepts: "arv" / "ARV"
- Accepts: "bedrooms" / "beds" / "Beds"
- Accepts: "tags" / "Tags"
- More: check `_normalize_row()` for all mappings

**Type Coercion:**
- Floats: ARV, asking_price, est_repairs, est_rent_monthly, mao, bathrooms
- Ints: bedrooms, sqft, timeline_days
- Tags: Pipe (|) or comma (,) separated strings → list

**Validation:**
- Every row validated against DealIn Pydantic model
- Errors collected (first 50) and returned with index + error message
- Row not added if validation fails

**Lead Source Forcing:**
- `lead_source` parameter overrides CSV/JSON value
- Prevents accidental misclassification of deal origin
- Default: "real" if not specified

**Audit Trail:**
- `DEALS_IMPORTED_JSON`: Logged with created count + forced_source
- `DEALS_IMPORTED_CSV`: Logged with created count + forced_source

---

## DB-7: Pipeline Summary (Dashboard)

### Purpose
Real-time deal pipeline dashboard. Computes:
- Deal counts by stage, source, country
- Top N scored deals (live scoring)
- Next actions for top deals (Cone-aware)

### Files Created

**[backend/app/core_gov/deals/summary_service.py](backend/app/core_gov/deals/summary_service.py)**
- `deals_summary(limit_scan, top_n)` — Compute full pipeline summary
  - Scans last `limit_scan` deals (default 3000)
  - Returns counts by stage, source, country
  - Scores top 800 deals, returns top `top_n` (default 15)
  - Computes next actions for each top deal

**[backend/app/core_gov/deals/summary_router.py](backend/app/core_gov/deals/summary_router.py)**
- `GET /core/deals/summary` — Pipeline dashboard endpoint

### Endpoint

```bash
curl "http://localhost:4000/core/deals/summary?limit_scan=3000&top_n=15"
```

**Response:**
```json
{
  "counts": {
    "total": 200,
    "by_stage": {
      "new": 70,
      "contacted": 50,
      "qualified": 40,
      "offer_sent": 25,
      "negotiating": 15
    },
    "by_source": {
      "seed": 100,
      "real": 80,
      "public": 20
    },
    "by_country": {
      "CA": 100,
      "US": 100
    }
  },
  "top_scored": [
    {
      "id": "uuid-1",
      "country": "CA",
      "province_state": "ON",
      "city": "Toronto",
      "strategy": "wholesale",
      "stage": "qualified",
      "lead_source": "real",
      "score": 89,
      "equity_pct": 42.5,
      "mao_suggested": 285000.00,
      "flags": []
    },
    {
      "id": "uuid-2",
      "country": "US",
      "province_state": "TX",
      "city": "Dallas",
      "strategy": "flip",
      "stage": "new",
      "lead_source": "public",
      "score": 85,
      "equity_pct": 38.0,
      "mao_suggested": 210000.00,
      "flags": ["heavy_repairs"]
    }
  ],
  "next_actions": [
    {
      "deal_id": "uuid-1",
      "priority": "high",
      "action": "send_offer",
      "why": "Qualified. Send MAO-based offer and schedule follow-up.",
      "band": "A"
    },
    {
      "deal_id": "uuid-2",
      "priority": "high",
      "action": "call_now",
      "why": "High score new lead. Contact immediately.",
      "band": "A"
    }
  ]
}
```

### Features

**Real-Time Scoring:**
- Scores top 800 deals on each request
- Returns top N sorted by score (descending)
- Includes: score, equity_pct, mao_suggested, flags

**Cone-Aware Actions:**
- Computes next action for each top deal
- Reads current Cone band
- Actions differ by band (A/B expansion vs C/D stabilization)

**Efficient:**
- Scans only last `limit_scan` deals (default 3000, not all 20K)
- Scores only 800 candidates (not all)
- Returns top 15 (configurable)

**Query Parameters:**
- `limit_scan`: How many recent deals to scan (default 3000)
- `top_n`: How many top deals to return (default 15)

---

## Complete Deal Bank System (DB-0 through DB-7)

| Component | Purpose | Endpoints |
|-----------|---------|-----------|
| DB-0 | Folder structure | — |
| DB-1 | Deal model + CRUD store | — |
| DB-2 | Deal CRUD router | POST /, GET /, GET /:id, PATCH /:id |
| DB-3 | Seed generator | POST /seed/generate |
| DB-4 | Scoring service | GET /:id/score |
| DB-5 | Next action service | GET /:id/next_action |
| **DB-6** | **Import/Export** | **POST /import/json, POST /import/csv, GET /export/json, GET /export/csv** |
| **DB-7** | **Pipeline Summary** | **GET /summary** |

**Total:** 13 endpoints across 9 components

---

## Integration Checklist

✅ Routers imported in core_router.py (lines 28-29)  
✅ Routers included in core router (lines 127-128)  
✅ Audit events: DEALS_IMPORTED_JSON, DEALS_IMPORTED_CSV  
✅ Syntax validation: 0 errors  
✅ File storage: Uses existing deals.json  
✅ Cone integration: deals_summary computes next_actions with band awareness  

---

## End-to-End Example

```bash
# 1. Seed 100 deals
curl -X POST "http://localhost:4000/core/deals/seed/generate?n=100&ca_ratio=0.5"

# 2. Check pipeline dashboard
curl "http://localhost:4000/core/deals/summary"

# 3. Export CSV (backup)
curl "http://localhost:4000/core/deals/export/csv?limit=50" > deals_backup.csv

# 4. Modify CSV locally (change strategy, stage, notes, etc.)

# 5. Re-import as "real" deals (forcing source)
curl -X POST "http://localhost:4000/core/deals/import/csv" \
  -H "Content-Type: application/json" \
  -d "{\"lead_source\": \"real\", \"csv\": \"$(cat deals_backup.csv | sed 's/\"/\\\\"/g')\"}"

# 6. Verify in dashboard (counts should update)
curl "http://localhost:4000/core/deals/summary" | jq '.counts'
```

---

## Testing Checklist

✅ POST /import/json (single item)  
✅ POST /import/json (multiple items)  
✅ POST /import/json (forced lead_source)  
✅ POST /import/json (error handling)  
✅ POST /import/csv (text upload)  
✅ POST /import/csv (header flexibility)  
✅ POST /import/csv (type coercion)  
✅ GET /export/json (all fields)  
✅ GET /export/csv (CSV format)  
✅ GET /summary (counts, top_scored, next_actions)  
✅ GET /summary (Cone-aware actions)  
✅ Audit trail logged  

---

## Summary

**DB-6 & DB-7** complete the Deal Bank foundation:

1. **Import/Export:** Bulk JSON/CSV with header flexibility, type coercion, lead_source forcing, validation
2. **Pipeline Summary:** Real-time dashboard with counts, top scored deals, Cone-aware next actions

**Ready for:**
- Bulk data ingestion from CRM/MLS
- Deal pipeline backup/restore
- Executive dashboards
- AI/human handoff decisions

All 9 Deal Bank components (DB-0 through DB-7) now complete and production-ready.
