# PACK_SPA_QUICK_REFERENCE.md

## Quick API Reference — P-CREDIT-1, P-PANTHEON-1, P-ANALYTICS-1

### P-CREDIT-1 Endpoints

#### 1. Get Credit Profile
```bash
curl -X GET http://localhost:5000/core/credit/profile
```

#### 2. Set/Update Credit Profile
```bash
curl -X POST http://localhost:5000/core/credit/profile \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Tech Startup Inc",
    "country": "US",
    "region": "CA",
    "entity_type": "corporation",
    "ein_sin_hint": "**-*234567",
    "has_business_bank": true,
    "has_duns": false,
    "has_gst_hst": false,
    "has_website": true,
    "has_business_phone": true,
    "notes": "Series A funded, 18 months old"
  }'
```

#### 3. Create Vendor/Tradeline
```bash
curl -X POST http://localhost:5000/core/credit/vendors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Amex Business Gold",
    "vendor_type": "bank_card",
    "country": "US",
    "requirements": ["$50k revenue", "12+ months business history"],
    "starter_limit": "$5,000",
    "notes": "Premium card, 1% cash back",
    "url_hint": "americanexpress.com/small-business",
    "status": "in_progress"
  }'
```

#### 4. List Vendors (with filters)
```bash
# All vendors
curl -X GET http://localhost:5000/core/credit/vendors

# Filter by status
curl -X GET "http://localhost:5000/core/credit/vendors?status=in_progress"

# Filter by type
curl -X GET "http://localhost:5000/core/credit/vendors?vendor_type=net30"

# Filter by country
curl -X GET "http://localhost:5000/core/credit/vendors?country=US"

# Combined
curl -X GET "http://localhost:5000/core/credit/vendors?status=planned&vendor_type=bank_card"
```

#### 5. Update Vendor
```bash
curl -X PATCH http://localhost:5000/core/credit/vendors/ven_a1b2c3d4e5f6 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "done",
    "notes": "Approved $25k limit"
  }'
```

#### 6. Create Credit Task
```bash
curl -X POST http://localhost:5000/core/credit/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Apply for Amex Business",
    "status": "in_progress",
    "due_date": "2026-02-01",
    "related_vendor_id": "ven_a1b2c3d4e5f6",
    "notes": "Gather last 3 months statements + tax returns"
  }'
```

#### 7. List Tasks (with filter)
```bash
# All tasks
curl -X GET http://localhost:5000/core/credit/tasks

# Filter by status
curl -X GET "http://localhost:5000/core/credit/tasks?status=planned"
```

#### 8. Update Task
```bash
curl -X PATCH http://localhost:5000/core/credit/tasks/ct_a1b2c3d4e5f6 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "done",
    "notes": "Card arrived, activated"
  }'
```

#### 9. Log Credit Score
```bash
curl -X POST http://localhost:5000/core/credit/scores \
  -H "Content-Type: application/json" \
  -d '{
    "bureau": "equifax",
    "score": 720,
    "note": "Personal (proxy for business credit)"
  }'
```

#### 10. List Score History
```bash
curl -X GET http://localhost:5000/core/credit/scores
```

#### 11. Get Recommendations
```bash
curl -X GET http://localhost:5000/core/credit/recommend
```

**Example Response:**
```json
{
  "stage": "tradelines",
  "actions": [
    "Open business bank account",
    "Confirm GST/HST registration (if applicable)",
    "Start Net-terms vendors (Net30/Net60) and pay early for 3 cycles",
    "Document everything in Vault + keep matching addresses"
  ],
  "next_vendors": [
    {
      "id": "ven_...",
      "name": "Amex",
      "vendor_type": "bank_card",
      "status": "planned"
    }
  ],
  "warnings": []
}
```

---

### P-PANTHEON-1 Endpoints

#### 1. Get Current Mode/State
```bash
curl -X GET http://localhost:5000/core/pantheon/state
```

**Response:**
```json
{
  "mode": "explore",
  "reason": "Initial seed state",
  "last_set_at": "2026-01-02T10:30:45.123456+00:00",
  "last_set_by": "seed"
}
```

#### 2. Switch Mode
```bash
# Switch to EXECUTE mode
curl -X POST http://localhost:5000/core/pantheon/mode \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "execute",
    "reason": "Production deployment - all checks passed"
  }'

# Switch back to EXPLORE mode
curl -X POST http://localhost:5000/core/pantheon/mode \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "explore",
    "reason": "Pausing for investigation"
  }'
```

#### 3. Dispatch Intent (Get Routing)
```bash
# Credit building intent
curl -X POST http://localhost:5000/core/pantheon/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "build business credit",
    "payload": {"priority": "high"},
    "desired_band": "B"
  }'

# Grant research
curl -X POST http://localhost:5000/core/pantheon/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "find grants for tech startups",
    "payload": {"industry": "SaaS"},
    "desired_band": "A"
  }'

# Loan recommendation
curl -X POST http://localhost:5000/core/pantheon/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "get loan recommendation",
    "desired_band": "C"
  }'

# Document management
curl -X POST http://localhost:5000/core/pantheon/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "upload and organize documents",
    "desired_band": "B"
  }'
```

**Response:**
```json
{
  "ok": true,
  "mode": "explore",
  "allowed": true,
  "band": "B",
  "route": "/core/credit/recommend",
  "suggestion": "[EXPLORE] Run credit recommend and build vendor/task plan",
  "warnings": []
}
```

---

### P-ANALYTICS-1 Endpoints

#### 1. Get Current Snapshot (no store)
```bash
curl -X GET http://localhost:5000/core/analytics/snapshot
```

**Response:**
```json
{
  "snapshot": {
    "id": "snap_a1b2c3d4e5f6",
    "created_at": "2026-01-02T10:30:45.123456+00:00",
    "metrics": {
      "deals.count": 42,
      "followups.count": 18,
      "buyers.count": 7,
      "grants.count": 150,
      "loans.count": 25,
      "vault.docs": 340,
      "know.docs": 89,
      "know.chunks": 456,
      "legal.rules": 32,
      "legal.profiles": 8,
      "comms.drafts": 12,
      "comms.sendlog": 145,
      "jv.partners": 3,
      "jv.links": 5,
      "property.count": 18,
      "credit.vendors": 14,
      "credit.tasks": 22,
      "credit.scores": 8,
      "credit.profile_set": 1
    },
    "warnings": []
  }
}
```

#### 2. Create and Store Snapshot
```bash
curl -X POST http://localhost:5000/core/analytics/snapshot
```

Same response as GET, but snapshot is now saved to history.json

#### 3. Get Snapshot History
```bash
# Last 50 snapshots (default)
curl -X GET http://localhost:5000/core/analytics/history

# Last 10 snapshots
curl -X GET "http://localhost:5000/core/analytics/history?limit=10"

# Last 100 snapshots
curl -X GET "http://localhost:5000/core/analytics/history?limit=100"
```

**Response:**
```json
{
  "items": [
    {
      "id": "snap_a1b2c3d4e5f6",
      "created_at": "2026-01-02T10:30:45.123456+00:00",
      "metrics": {...},
      "warnings": []
    },
    {
      "id": "snap_z9y8x7w6v5u4",
      "created_at": "2026-01-02T10:20:30.654321+00:00",
      "metrics": {...},
      "warnings": []
    }
  ]
}
```

---

## Common Workflows

### Workflow 1: Build Business Credit (Credit + Pantheon)

```bash
# 1. Check system readiness
curl -X GET http://localhost:5000/core/pantheon/state

# 2. Set up business profile
curl -X POST http://localhost:5000/core/credit/profile \
  -d '{"business_name":"My Co","country":"US","entity_type":"LLC"}'

# 3. Add target vendors
curl -X POST http://localhost:5000/core/credit/vendors \
  -d '{"name":"Stripe","vendor_type":"net30"}'

# 4. Get recommendations
curl -X GET http://localhost:5000/core/credit/recommend

# 5. Check mode before proceeding
curl -X POST http://localhost:5000/core/pantheon/dispatch \
  -d '{"intent":"build credit","desired_band":"B"}'
```

### Workflow 2: System Health Check (Analytics)

```bash
# Check current state
curl -X GET http://localhost:5000/core/analytics/snapshot

# Save it for comparison
curl -X POST http://localhost:5000/core/analytics/snapshot

# Compare with previous
curl -X GET "http://localhost:5000/core/analytics/history?limit=2"
```

### Workflow 3: Mode-Safe Operations (Pantheon)

```bash
# Start in EXPLORE mode
curl -X GET http://localhost:5000/core/pantheon/state

# Try operation (mode-aware)
curl -X POST http://localhost:5000/core/pantheon/dispatch \
  -d '{"intent":"apply for loan","desired_band":"D"}'

# Switch to EXECUTE when ready
curl -X POST http://localhost:5000/core/pantheon/mode \
  -d '{"mode":"execute","reason":"All checks passed"}'

# Retry operation in EXECUTE
curl -X POST http://localhost:5000/core/pantheon/dispatch \
  -d '{"intent":"apply for loan","desired_band":"D"}'
```

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (validation error) |
| 404 | Not found (vendor/task doesn't exist) |
| 500 | Server error |

---

## Notes

- All timestamps are **UTC ISO format** (e.g., `2026-01-02T10:30:45.123456+00:00`)
- IDs are auto-generated with semantic prefixes: `ven_`, `ct_`, `sc_`, `snap_`
- All endpoints are **read + write safe** (file-backed with atomic write)
- No authentication in v1 (add via middleware later)
- Data persists in `backend/data/{module}/` directory
