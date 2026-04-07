# PACK 1, 2, 3 - API Quick Reference

All endpoints prefixed with `/core/` and available immediately on startup.

## PACK 1: Communications Hub (`/core/comms`)

### Create Draft
```
POST /core/comms/drafts
Content-Type: application/json

{
  "channel": "sms",
  "subject": "Email subject",
  "to": "+1234567890 or email@example.com",
  "body": "Message content (required)",
  "deal_id": "deal_001",
  "contact_id": "contact_001",
  "tone": "calm|firm|friendly",
  "status": "draft",
  "tags": ["urgent", "followup"],
  "meta": {"custom_field": "value"}
}

Response: 201
{
  "id": "dr_xxxxx",
  "channel": "sms",
  "to": "+1234567890",
  "body": "Message content",
  "status": "draft",
  "created_at": "2026-01-03T...",
  "updated_at": "2026-01-03T..."
}
```

### List Drafts
```
GET /core/comms/drafts?status=draft&channel=sms&deal_id=deal_001&contact_id=contact_001
Response: 200
{
  "items": [...]
}
```

### Get Single Draft
```
GET /core/comms/drafts/{draft_id}
Response: 200
{
  "id": "dr_xxxxx",
  ...
}
```

### Update Draft
```
PATCH /core/comms/drafts/{draft_id}
Content-Type: application/json

{
  "body": "Updated message",
  "status": "ready",
  "tags": ["sent", "followup"],
  "meta": {"updated": true}
}

Response: 200
```

### Mark as Sent (Create Send Log Entry)
```
POST /core/comms/drafts/{draft_id}/mark_sent?provider=twilio&provider_ref=msg_123
Response: 200
{
  "id": "sl_xxxxx",
  "draft_id": "dr_xxxxx",
  "provider": "twilio",
  "provider_ref": "msg_123",
  "created_at": "2026-01-03T..."
}
```

### Get Send Log (History)
```
GET /core/comms/sendlog?limit=50&channel=sms&deal_id=deal_001
Response: 200
{
  "items": [
    {
      "id": "sl_xxxxx",
      "draft_id": "dr_xxxxx",
      "channel": "sms",
      "to": "+1234567890",
      "body": "...",
      "provider": "manual_copy",
      "created_at": "2026-01-03T..."
    },
    ...
  ]
}
```

---

## PACK 2: Partner/JV Manager (`/core/jv`)

### Create Partner
```
POST /core/jv/partners
Content-Type: application/json

{
  "name": "Partner Name (required)",
  "role": "jv_partner|buyer|lender|gc|pm|agent|other",
  "status": "active|paused|archived",
  "email": "contact@partner.com",
  "phone": "+1234567890",
  "notes": "Partner background",
  "tags": ["tier-1", "verified"],
  "meta": {"custom": "data"}
}

Response: 201
{
  "id": "p_xxxxx",
  "name": "Partner Name",
  "role": "jv_partner",
  "status": "active",
  "created_at": "2026-01-03T...",
  "updated_at": "2026-01-03T..."
}
```

### List Partners
```
GET /core/jv/partners?status=active&role=jv_partner&tag=tier-1
Response: 200
{
  "items": [...]
}
```

### Get Partner
```
GET /core/jv/partners/{partner_id}
Response: 200
```

### Update Partner
```
PATCH /core/jv/partners/{partner_id}
Content-Type: application/json

{
  "status": "paused",
  "phone": "+9876543210",
  "tags": ["tier-2"]
}

Response: 200
```

### Create Deal Link
```
POST /core/jv/links
Content-Type: application/json

{
  "partner_id": "p_xxxxx",
  "deal_id": "deal_001",
  "relationship": "JV",
  "split_notes": "50/50 profit split, equal capital",
  "status": "active",
  "meta": {"equity": 0.5}
}

Response: 201
{
  "id": "lnk_xxxxx",
  "partner_id": "p_xxxxx",
  "deal_id": "deal_001",
  "relationship": "JV",
  "status": "active",
  "created_at": "2026-01-03T..."
}
```

### List Links
```
GET /core/jv/links?partner_id=p_xxxxx&deal_id=deal_001&status=active
Response: 200
{
  "items": [...]
}
```

### Update Link
```
PATCH /core/jv/links/{link_id}
Content-Type: application/json

{
  "split_notes": "Updated split",
  "status": "archived"
}

Response: 200
```

### Partner Dashboard (Read-Only)
```
GET /core/jv/partners/{partner_id}/dashboard
Response: 200
{
  "partner": {
    "id": "p_xxxxx",
    "name": "Partner Name",
    ...
  },
  "links": [
    {
      "id": "lnk_xxxxx",
      "deal_id": "deal_001",
      "relationship": "JV",
      ...
    }
  ],
  "deal_summaries": [
    {
      "deal_id": "deal_001",
      "address": "123 Main St",
      "status": "active",
      "price": 500000,
      "arv": 650000
    }
  ]
}
```

---

## PACK 3: Property Intelligence (`/core/property`)

### Create Property
```
POST /core/property/properties
Content-Type: application/json

{
  "address": "123 Main St (required)",
  "country": "CA|US",
  "region": "ON|CA|NY etc",
  "city": "Toronto",
  "postal": "M5V 3A8",
  "status": "tracked|analyzing|offered|under_contract|sold|archived",
  "deal_id": "deal_001",
  "meta": {"lot_size": "0.25 acres"}
}

Response: 201
{
  "id": "pr_xxxxx",
  "address": "123 Main St",
  "country": "CA",
  "region": "ON",
  "status": "tracked",
  "created_at": "2026-01-03T..."
}
```

### List Properties
```
GET /core/property/properties?status=analyzing&country=CA&region=ON
Response: 200
{
  "items": [...]
}
```

### Get Property
```
GET /core/property/properties/{property_id}
Response: 200
```

### Update Property
```
PATCH /core/property/properties/{property_id}
Content-Type: application/json

{
  "status": "offered",
  "city": "Toronto",
  "deal_id": "deal_002"
}

Response: 200
```

### Set/Update Neighborhood Rating
```
POST /core/property/properties/{property_id}/neighborhood_rating
Content-Type: application/json

{
  "score": 85,
  "notes": "Great walkability",
  "factors": {
    "walkability": 9,
    "transit": 8,
    "schools": 9,
    "shopping": 7
  }
}

Response: 200
{
  "property_id": "pr_xxxxx",
  "score": 85,
  "notes": "Great walkability",
  "updated_at": "2026-01-03T..."
}
```

### Get Neighborhood Rating
```
GET /core/property/properties/{property_id}/neighborhood_rating
Response: 200
```

### Save Comparable Properties Request (v1 Stub)
```
POST /core/property/comps
Content-Type: application/json

{
  "property_id": "pr_xxxxx",
  "radius_km": 2.0,
  "beds": 3,
  "baths": 2,
  "notes": "Looking for similar 3BR/2BA"
}

Response: 200
{
  "ok": true,
  "property_id": "pr_xxxxx",
  "comps": [],
  "notes": "Looking for similar 3BR/2BA"
}
```

### Get Comparable Properties
```
GET /core/property/properties/{property_id}/comps
Response: 200
{
  "property_id": "pr_xxxxx",
  "radius_km": 2.0,
  "beds": 3,
  "baths": 2,
  "comps": [],
  "updated_at": "2026-01-03T..."
}
```

### Set/Update Repair & Rent Estimates
```
POST /core/property/properties/{property_id}/repair_rent
Content-Type: application/json

{
  "est_repairs": 25000.00,
  "est_rent": 2500.00,
  "assumptions": {
    "cap_rate": 0.06,
    "exit_year": 5,
    "noi_margin": 0.4
  }
}

Response: 200
{
  "property_id": "pr_xxxxx",
  "est_repairs": 25000.0,
  "est_rent": 2500.0,
  "updated_at": "2026-01-03T..."
}
```

### Get Repair & Rent Estimates
```
GET /core/property/properties/{property_id}/repair_rent
Response: 200
{
  "property_id": "pr_xxxxx",
  "est_repairs": 25000.0,
  "est_rent": 2500.0,
  "assumptions": {...},
  "updated_at": "2026-01-03T..."
}
```

---

## Error Responses

### 400 Bad Request (Validation)
```json
{
  "detail": "body is required"
}
```

### 404 Not Found
```json
{
  "detail": "draft not found"
}
```

### 500 Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Data Formats

**Channel types:** sms, email, call, dm, letter, other
**Statuses (Comms):** draft, ready, sent, archived
**Statuses (Property):** tracked, analyzing, offered, under_contract, sold, archived
**Roles (JV):** buyer, lender, gc, pm, jv_partner, agent, other
**Countries:** CA (Canada), US (United States)

All timestamps are ISO 8601 UTC format: `2026-01-03T01:59:26.849663+00:00`
All IDs are prefixed: `dr_`, `sl_`, `p_`, `lnk_`, `pr_`

---

## Testing

Run smoke tests:
```bash
python backend/tests/smoke_packs_1_2_3.py
```

Or use the test file:
```bash
python test_packs.py
```
