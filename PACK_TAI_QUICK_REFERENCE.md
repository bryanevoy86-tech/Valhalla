# PACK TAI Quick Reference

## Endpoints at a Glance

### Trust Endpoints (6)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/core/trust/entities` | Create entity |
| GET | `/core/trust/entities` | List entities (filter by status, country, entity_type, tag) |
| GET | `/core/trust/entities/{id}` | Get entity |
| PATCH | `/core/trust/entities/{id}` | Update entity |
| POST | `/core/trust/entities/{id}/milestones/upsert` | Upsert milestone (auto-followup integration) |
| GET | `/core/trust/summary` | Summary stats |

### Audit Endpoints (2)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/core/audit/event` | Log event (append-only) |
| GET | `/core/audit/events` | List events (filter by level, event_type, ref_id) |

### Integrity Endpoints (1)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/core/integrity/check` | Run health check |

---

## Example Workflows

### Setup Panama Master Trust

```bash
# 1. Create master trust entity
MASTER=$(curl -s -X POST http://localhost:8000/core/trust/entities \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Panama Master Trust 2026",
    "entity_type": "trust",
    "country": "PA",
    "description": "Main trust structure",
    "status": "in_progress",
    "tags": ["panama", "master"]
  }')

MASTER_ID=$(echo $MASTER | jq -r '.id')

# 2. Add milestones (corp, bank, insurance, etc.)
curl -s -X POST http://localhost:8000/core/trust/entities/$MASTER_ID/milestones/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "key": "corp_setup",
    "title": "Corp Registered",
    "status": "not_started",
    "due_date": "2026-02-15"
  }' | jq

# 3. Check status
curl -s http://localhost:8000/core/trust/summary | jq
```

### Log Audit Trail

```bash
# Log a key decision
curl -s -X POST http://localhost:8000/core/audit/event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "cone_decision",
    "level": "info",
    "message": "Panama trust strategy approved by executive",
    "actor": "user:john@example.com",
    "ref_type": "entity",
    "ref_id": "ent_xyz123"
  }' | jq

# View recent audit trail
curl -s "http://localhost:8000/core/audit/events?limit=20&event_type=cone_decision" | jq '.items[] | {message, actor, created_at}'
```

### System Health Check

```bash
# Run integrity check
RESULT=$(curl -s http://localhost:8000/core/integrity/check)

echo "Overall status: $(echo $RESULT | jq '.ok')"
echo "Checks run: $(echo $RESULT | jq '.checks_run')"
echo "Passed: $(echo $RESULT | jq '.passed')"
echo "Failed: $(echo $RESULT | jq '.failed')"

# Show failures
echo $RESULT | jq '.results[] | select(.ok == false)'
```

---

## Data Structures

### Entity Record
```json
{
  "id": "ent_a1b2c3d4e5f6",
  "name": "Panama Master Trust 2026",
  "entity_type": "trust",
  "country": "PA",
  "region": "",
  "description": "Main trust structure",
  "status": "in_progress",
  "tags": ["panama", "master"],
  "milestones": [
    {
      "key": "corp_setup",
      "title": "Corp Registered",
      "status": "in_progress",
      "due_date": "2026-02-15",
      "notes": "",
      "updated_at": "2026-01-02T12:34:56Z"
    }
  ],
  "meta": {},
  "created_at": "2026-01-02T12:00:00Z",
  "updated_at": "2026-01-02T12:34:56Z"
}
```

### Audit Event
```json
{
  "id": "ae_x1y2z3a4b5c6",
  "event_type": "cone_decision",
  "level": "info",
  "message": "Panama trust strategy approved",
  "actor": "user:john@example.com",
  "ref_type": "entity",
  "ref_id": "ent_a1b2c3d4e5f6",
  "meta": {},
  "created_at": "2026-01-02T12:34:56Z"
}
```

### Check Result
```json
{
  "ok": true,
  "checks_run": 12,
  "passed": 11,
  "failed": 1,
  "results": [
    {"check": "json_file", "path": "backend/data/trust/entities.json", "ok": true, "note": "ok"},
    {"check": "json_file", "path": "backend/data/deals.json", "ok": false, "note": "missing"},
    {"check": "tmp_files", "ok": true, "note": "none"}
  ]
}
```

---

## Query Parameters

### Trust List Filters
```bash
# By status
?status=in_progress

# By country
?country=PA

# By entity type
?entity_type=trust

# By tag
?tag=panama

# Combinations
?status=blocked&country=PA
```

### Audit List Filters
```bash
# By limit (default 100, max 500)
?limit=50

# By level
?level=error

# By event type
?event_type=cone_decision

# By ref_id
?ref_id=ent_xyz123

# Combinations
?limit=100&level=warn&event_type=mode_switch
```

---

## Common Tasks

### Update Entity Status
```bash
curl -X PATCH http://localhost:8000/core/trust/entities/{id} \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

### Add Tags to Entity
```bash
curl -X PATCH http://localhost:8000/core/trust/entities/{id} \
  -H "Content-Type: application/json" \
  -d '{"tags": ["panama", "master", "active"]}'
```

### Mark Milestone Done
```bash
curl -X POST http://localhost:8000/core/trust/entities/{id}/milestones/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "key": "corp_setup",
    "title": "Corp Registered",
    "status": "done"
  }'
# Note: This auto-updates entity status if all milestones done
```

### Log Mode Switch
```bash
curl -X POST http://localhost:8000/core/audit/event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "mode_switch",
    "level": "info",
    "message": "Switched to Panama strategy mode",
    "actor": "system"
  }'
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success (GET, PATCH) |
| 201 | Created (POST) |
| 400 | Bad request (missing fields, invalid data) |
| 404 | Not found (entity/event doesn't exist) |
| 500 | Server error |

---

## Entity Types & Countries

### Entity Types
- corp, llc, sole_prop, trust, bank, insurance, other

### Countries
- CA (Canada)
- US (USA)
- PA (Panama)
- BS (Bahamas)
- PH (Philippines)
- NZ (New Zealand)
- AE (UAE)
- UK (United Kingdom)
- OTHER

### Statuses
- not_started, in_progress, done, blocked

---

## Tips & Tricks

1. **Milestone Auto-Rollup**: If all milestones are "done", entity status auto-becomes "done"
2. **Milestone Due Dates**: If set, auto-creates followup task (optional integration)
3. **Tag Deduplication**: Duplicates auto-removed on create/update
4. **Audit Immutable**: Events never updated, only appended
5. **Audit Cap**: Auto-purges oldest events after 5000
6. **Integrity Check**: Run before backups to ensure data consistency

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 404 on trust endpoints | Check core_router.py imports + includes |
| Entity milestones not sorting | Key must be unique and properly formatted |
| Audit events disappearing | Normal if >5000 events (oldest purged) |
| Integrity check failing | Run manually to see which files are missing |
| Followup not created | Check due_date format (must be valid) |

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-02
