# Quick Reference — PACK 1-3 Deployment

## What Was Built

**P-INVENTORY-1** — Pantry/Stock Registry  
Track household items with thresholds, cadence, locations, and costs

**P-INVENTORY-2** — Reorder Suggestions  
Auto-compute which items need reordering based on thresholds or time cadence

**P-AUTOMATE-3** — Auto-create Followups  
Generate followups for upcoming bills and low-stock items (with deduplication)

---

## Quick Test

All systems tested and passing:
```bash
cd C:\dev\valhalla
python -m pytest test_pack_inventory_automate3_unit.py -v
# Result: 21 passed in 0.55s ✅
```

---

## API Examples

### Create Inventory Item
```bash
curl -X POST http://localhost:8000/core/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Toilet Paper",
    "location":"bathroom",
    "unit":"roll",
    "on_hand":6,
    "min_threshold":4,
    "reorder_qty":12,
    "priority":"high",
    "preferred_store":"Costco",
    "est_unit_cost":1.10,
    "tags":["household"]
  }'
```

### Consume Stock
```bash
curl -X POST http://localhost:8000/core/inventory/{item_id}/adjust \
  -H "Content-Type: application/json" \
  -d '{"delta":-3,"reason":"weekly use"}'
```

### Get Reorder Suggestions
```bash
curl "http://localhost:8000/core/inventory/reorders/suggest?max_items=10"
```

### Generate Followups (Explore)
```bash
curl -X POST http://localhost:8000/core/automation_actions/generate_followups \
  -H "Content-Type: application/json" \
  -d '{"mode":"explore","lookahead_days":14}'
```

---

## File Locations

### Inventory Module
```
backend/app/core_gov/inventory/
├── __init__.py       ← exports inventory_router
├── schemas.py        ← 6 data models
├── store.py          ← JSON persistence
├── service.py        ← 5 service functions
├── router.py         ← 6 REST endpoints
└── reorder.py        ← reorder suggestion algorithm
```

### Automation Module
```
backend/app/core_gov/automation_actions/
├── __init__.py       ← exports automation_actions_router
├── schemas.py        ← 2 data models
├── store.py          ← dedupe.json persistence
├── service.py        ← generate_followups function
└── router.py         ← 1 REST endpoint
```

### Data Files
```
backend/data/inventory/
├── items.json        ← all inventory items
└── logs.json         ← adjustment log (max 500)

backend/data/automation_actions/
└── dedupe.json       ← dedup tracking (max 800, 21-day window)
```

---

## Data Structures

### Inventory Item
```json
{
  "id": "iv_abc123def456",
  "name": "Item name",
  "location": "pantry|garage|fridge|etc",
  "unit": "count|roll|box|lb|kg|etc",
  "on_hand": 10.0,
  "min_threshold": 5.0,
  "reorder_qty": 20.0,
  "cadence_days": 30,
  "priority": "low|normal|high|critical",
  "preferred_brand": "Brand name",
  "preferred_store": "Store name",
  "est_unit_cost": 2.50,
  "tags": ["tag1", "tag2"],
  "notes": "Notes",
  "last_purchased": "2025-01-02T15:30:00Z",
  "created_at": "2025-01-03T10:00:00Z"
}
```

### Reorder Suggestion
```json
{
  "item_id": "iv_abc123",
  "name": "Item name",
  "location": "pantry",
  "priority": "high",
  "on_hand": 2,
  "min_threshold": 4,
  "reorder_qty": 12,
  "reasons": ["below_threshold", "cadence_due"],
  "est_unit_cost": 1.10,
  "est_total_cost": 13.20,
  "days_since_last_purchased": 5
}
```

### Followup Generated
```json
{
  "id": "fu_abc123def456",
  "title": "Reorder: Toilet Paper",
  "status": "open",
  "due_date": "2025-01-05",
  "priority": "high",
  "source": "automation_actions",
  "meta": {
    "kind": "reorder",
    "reorder": {...}
  }
}
```

---

## Key Features

### Inventory
- ✅ Item creation with multiple attributes
- ✅ Location-based grouping (pantry, garage, etc.)
- ✅ Unit types (count, roll, box, lb, kg, ml, etc.)
- ✅ Priority levels for sorting
- ✅ Tag-based filtering
- ✅ Preferred brand/store tracking
- ✅ Cost estimation for budgeting
- ✅ Stock adjustment logging

### Reorder Suggestions
- ✅ Threshold-based detection
- ✅ Cadence-based detection (time intervals)
- ✅ Cost estimation per item
- ✅ Multi-level filtering
- ✅ Priority-based sorting
- ✅ Fallback heuristics

### Auto-Create Followups
- ✅ Bill-based followups
- ✅ Reorder-based followups
- ✅ Safe-call pattern (missing modules don't break)
- ✅ Explore mode (dry-run)
- ✅ Execute mode (actual creation)
- ✅ Deduplication with time window
- ✅ Warning collection

---

## Filters Supported

### Inventory List
```bash
?location=pantry
?priority=high
?tag=household
?location=pantry&priority=high
```

### Reorder Suggestions
```bash
?location=garage
?priority=critical
?tag=household
?max_items=25
```

### Followup Generation
```
lookahead_days: 14 (default)
dedupe_days: 21 (default)
max_create: 30 (default)
mode: "explore" | "execute"
```

---

## UUID Prefixes

| Prefix | Meaning | Example |
|--------|---------|---------|
| iv_ | Inventory item | iv_abc123def456 |
| il_ | Inventory log | il_xyz789abc123 |
| dd_ | Dedupe entry | dd_abc123456 |
| fu_ | Followup | fu_def456ghi789 |

---

## Test Coverage

**21 unit tests total:**
- 8 inventory tests
- 4 reorder tests
- 7 automation action tests
- 2 integration tests

**All passing:** ✅ 21/21

Run tests:
```bash
python -m pytest test_pack_inventory_automate3_unit.py -v
```

---

## Deployment Checklist

- ✅ 11 module files created
- ✅ 6 new API endpoints
- ✅ 3 data stores created
- ✅ All routers wired
- ✅ 21 tests passing
- ✅ Documentation complete
- ✅ Production ready

---

## Status

**Deployment Date:** January 3, 2026  
**Status:** ✅ COMPLETE  
**Test Pass Rate:** 100% (21/21)  
**Ready For:** Production deployment

For full details, see: [SESSION4_PACK1_3_COMPLETE.md](SESSION4_PACK1_3_COMPLETE.md)
