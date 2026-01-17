# P-BSE Quick Reference

## Endpoints at a Glance

### Boring Cash Engines

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/core/boring/engines` | Create new engine |
| GET | `/core/boring/engines` | List all engines |
| GET | `/core/boring/engines/{id}` | Get engine details |
| PATCH | `/core/boring/engines/{id}` | Update engine |
| POST | `/core/boring/runs` | Create new run |
| GET | `/core/boring/runs` | List runs |
| PATCH | `/core/boring/runs/{id}` | Update run |
| GET | `/core/boring/summary` | Get engine summary |

### Shield Defense System

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/core/shield/config` | Get current config |
| POST | `/core/shield/config` | Update config |
| POST | `/core/shield/evaluate` | Evaluate health state |

### Master Exporter

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/core/export/backup` | Create backup |
| GET | `/core/export/backups` | List backups |
| GET | `/core/export/backup/{id}` | Get backup info |
| GET | `/core/export/backup/{id}/download` | Download backup zip |

---

## Example Workflows

### Create and Track a Boring Engine

```bash
# 1. Create engine
RESPONSE=$(curl -s -X POST http://localhost:8000/core/boring/engines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Landscaping Service",
    "revenue_forecast_monthly": 8000,
    "cost_estimated_monthly": 3000,
    "tags": ["seasonal", "summer"]
  }')

ENGINE_ID=$(echo $RESPONSE | jq -r '.id')

# 2. Create first run
curl -s -X POST http://localhost:8000/core/boring/runs \
  -H "Content-Type: application/json" \
  -d "{\"engine_id\": \"$ENGINE_ID\"}" | jq

# 3. Update run status
RUN_ID="run-20240115..."
curl -s -X PATCH http://localhost:8000/core/boring/runs/$RUN_ID \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}' | jq

# 4. View summary
curl -s http://localhost:8000/core/boring/summary | jq
```

### Monitor Defense Tier

```bash
# 1. Get current config
curl -s http://localhost:8000/core/shield/config | jq

# 2. Evaluate health (reserve = $45k, pipeline = 3 deals)
curl -s -X POST http://localhost:8000/core/shield/evaluate \
  -H "Content-Type: application/json" \
  -d '{"current_reserve": 45000, "pipeline_deal_count": 3}' | jq

# Expected output if thresholds breached:
# {
#   "current_tier": "orange",
#   "recommended_actions": ["pause_new_deals", "hold_distribution"],
#   "breach_reason": "reserve_floor_breach"
# }

# 3. Update config if needed
curl -s -X POST http://localhost:8000/core/shield/config \
  -H "Content-Type: application/json" \
  -d '{
    "reserve_floor_amount": 60000,
    "pipeline_minimum_deals": 5
  }' | jq
```

### Create and Download Backup

```bash
# 1. Trigger backup
BACKUP=$(curl -s -X POST http://localhost:8000/core/export/backup)
BACKUP_ID=$(echo $BACKUP | jq -r '.id')

echo "Backup created: $BACKUP_ID"
echo "Size: $(echo $BACKUP | jq '.file_size') bytes"
echo "Files: $(echo $BACKUP | jq '.file_count') JSON files"

# 2. List recent backups
curl -s "http://localhost:8000/core/export/backups?limit=5" | jq '.backups[] | {id, timestamp, file_size}'

# 3. Download specific backup
curl -O "http://localhost:8000/core/export/backup/$BACKUP_ID/download"

# 4. Extract zip
unzip backup-*.zip
```

---

## Data Structures

### Boring Engine
```json
{
  "id": "boring-20240115120530",
  "name": "Landscaping Service",
  "status": "active",
  "revenue_forecast_monthly": 8000,
  "cost_estimated_monthly": 3000,
  "tags": ["seasonal", "summer"],
  "followup_integration": null,
  "created_at": "2024-01-15T12:05:30Z",
  "updated_at": "2024-01-15T12:05:30Z"
}
```

### Run Record
```json
{
  "id": "run-20240115120545",
  "engine_id": "boring-20240115120530",
  "status": "active",
  "created_at": "2024-01-15T12:05:45Z",
  "updated_at": "2024-01-15T12:05:45Z"
}
```

### Shield Config
```json
{
  "tiers": {
    "green": ["notify_board"],
    "yellow": ["pause_new_deals", "notify_board"],
    "orange": ["pause_new_deals", "hold_distribution", "notify_board"],
    "red": ["pause_new_deals", "hold_distribution", "restrict_funding", "trigger_audit"]
  },
  "reserve_floor_amount": 50000,
  "pipeline_minimum_deals": 5,
  "updated_at": "2024-01-15T12:05:30Z"
}
```

### Evaluate Response
```json
{
  "current_tier": "yellow",
  "recommended_actions": ["pause_new_deals"],
  "breach_reason": "pipeline_minimum_breach"
}
```

### Backup Result
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T12:05:30Z",
  "filename": "backup-20240115-120530.zip",
  "file_size": 1048576,
  "file_count": 127,
  "created_at": "2024-01-15T12:05:30Z"
}
```

---

## Key Features

### Boring Module
- ✅ Automatic engine registry with status tracking
- ✅ Job run tracking with automatic creation
- ✅ Tag deduplication to prevent duplicates
- ✅ Revenue/cost forecasting per engine
- ✅ Optional followup system integration
- ✅ Engine summary statistics

### Shield Module
- ✅ Multi-tier defense (green/yellow/orange/red)
- ✅ Automatic tier escalation on breach
- ✅ Reserve floor monitoring
- ✅ Pipeline minimum enforcement
- ✅ Configurable action mappings
- ✅ Health evaluation API

### Exporter Module
- ✅ Recursive JSON file discovery
- ✅ Automatic zip archive creation
- ✅ Backup history tracking (capped 200)
- ✅ Download support via FileResponse
- ✅ Deduplication to prevent re-backups
- ✅ Automatic exclusion of export folder

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| 404 on boring endpoints | Check core_router.py has boring_router import + include_router call |
| JSON files missing | Modules auto-create on first write; manually create `[]` if needed |
| Shield evaluate returns unexpected tier | Check reserve_floor_amount and pipeline_minimum_deals settings |
| Backup download returns empty | Ensure backend/data/ has JSON files; check exports folder exists |
| Port 8000 already in use | Change port: `uvicorn app.main:app --port 8001` |

---

## Configuration Checklist

- [ ] Verify 14 files created in boring/, shield/, exporter/
- [ ] Confirm core_router.py wired (3 imports + 3 includes)
- [ ] Run py_compile on all files
- [ ] Set reserve_floor_amount in Shield config
- [ ] Set pipeline_minimum_deals in Shield config
- [ ] Create backend/data/boring/ directory
- [ ] Create backend/data/shield/ directory
- [ ] Create backend/data/exports/backups/ directory
- [ ] Test POST /core/boring/engines endpoint
- [ ] Test POST /core/shield/evaluate endpoint
- [ ] Test POST /core/export/backup endpoint

---

## Performance Tips

1. **Boring**: Cache engine list in memory if >100 engines
2. **Shield**: Pre-compute tier escalation logic if evaluate called frequently
3. **Exporter**: Compress exports folder separately to avoid large backups
4. **General**: Add database layer later if JSON gets too large (>100MB)

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: 2024-01-15
