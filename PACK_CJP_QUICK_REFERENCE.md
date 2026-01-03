# P-CJP Three-Pack Quick Reference

## Communication Hub (`/core/comms/*`)

### Create Draft Message
```bash
curl -X POST http://localhost:5000/core/comms/drafts \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "sms",
    "to": "+14165551234",
    "subject": "Deal Update",
    "body": "Your message here",
    "deal_id": "d_123",
    "contact_id": "c_456",
    "buyer_id": "b_789",
    "tags": ["urgent", "follow-up"],
    "meta": {}
  }'
```

### List Drafts
```bash
# All drafts
curl "http://localhost:5000/core/comms/drafts"

# Filter by status (draft, ready, sent, failed, archived)
curl "http://localhost:5000/core/comms/drafts?status=draft"

# Filter by channel (sms, email, call, dm, letter)
curl "http://localhost:5000/core/comms/drafts?channel=email"

# Filter by deal
curl "http://localhost:5000/core/comms/drafts?deal_id=d_123"
```

### Update Draft
```bash
curl -X PATCH http://localhost:5000/core/comms/drafts/msg_abc123 \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+1-new-number",
    "subject": "Updated subject",
    "body": "Updated body",
    "tags": ["priority"],
    "status": "ready"
  }'
```

### Mark as Sent
```bash
# Success
curl -X POST "http://localhost:5000/core/comms/drafts/msg_abc123/mark_sent?ok=true" \
  -H "Content-Type: application/json" \
  -d '{
    "sent_via": "twilio",
    "external_id": "SM1234567890abcdef",
    "note": "Delivered successfully"
  }'

# Failed
curl -X POST "http://localhost:5000/core/comms/drafts/msg_abc123/mark_sent?ok=false" \
  -H "Content-Type: application/json" \
  -d '{
    "sent_via": "twilio",
    "external_id": "SM1234567890abcdef",
    "note": "Number not in service"
  }'
```

### Get Send Log
```bash
# All logs
curl "http://localhost:5000/core/comms/sendlog"

# Logs for specific draft
curl "http://localhost:5000/core/comms/sendlog?draft_id=msg_abc123"
```

---

## Partner/JV Management (`/core/jv/*`)

### Create Partner
```bash
curl -X POST http://localhost:5000/core/jv/partners \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ABC Investments Ltd",
    "partner_type": "jv",
    "status": "active",
    "email": "partners@abc.com",
    "phone": "+14165551234",
    "notes": "Active JV partner since 2024",
    "tags": ["jv", "residential", "gta"],
    "meta": {"net_worth": "5M+"}
  }'
```

### List Partners
```bash
# All partners
curl "http://localhost:5000/core/jv/partners"

# Filter by status (active, paused, blocked)
curl "http://localhost:5000/core/jv/partners?status=active"

# Filter by type (buyer, lender, jv, vendor, agent, other)
curl "http://localhost:5000/core/jv/partners?partner_type=buyer"

# Filter by tag
curl "http://localhost:5000/core/jv/partners?tag=residential"
```

### Get Partner Details
```bash
curl "http://localhost:5000/core/jv/partners/par_abc123"
```

### Link Deal to Partner
```bash
curl -X POST "http://localhost:5000/core/jv/partners/par_abc123/link_deal?deal_id=d_xyz&role=co_buyer&split=50/50&notes=Equal partners" \
  -H "Content-Type: application/json"
```

### Get Partner Dashboard
```bash
curl "http://localhost:5000/core/jv/partners/par_abc123/dashboard"

# Response:
{
  "partner": { /* partner record */ },
  "deals": [
    {
      "partner_id": "par_abc123",
      "deal_id": "d_xyz",
      "role": "co_buyer",
      "split": "50/50",
      "notes": "Equal partners",
      "created_at": "2026-01-02T..."
    }
  ],
  "computed": {
    "linked_deals": 1,
    "deals_loaded": 1
  },
  "warnings": []
}
```

### List Links
```bash
# All links
curl "http://localhost:5000/core/jv/links"

# By partner
curl "http://localhost:5000/core/jv/links?partner_id=par_abc123"

# By deal
curl "http://localhost:5000/core/jv/links?deal_id=d_xyz"
```

---

## Property Intelligence (`/core/property/*`)

### Create Property
```bash
curl -X POST http://localhost:5000/core/property/ \
  -H "Content-Type: application/json" \
  -d '{
    "country": "CA",
    "region": "ON",
    "city": "Toronto",
    "address": "123 Main St",
    "postal": "M5H 2N2",
    "beds": 3,
    "baths": 2.0,
    "sqft": 1800,
    "year_built": 1995,
    "deal_id": "d_123",
    "tags": ["residential", "multi-unit"],
    "meta": {"mls": "N123456"}
  }'
```

### List Properties
```bash
# All properties
curl "http://localhost:5000/core/property/"

# Filter by country (CA, US)
curl "http://localhost:5000/core/property/?country=CA"

# Filter by region (province/state code)
curl "http://localhost:5000/core/property/?region=ON"

# Filter by deal
curl "http://localhost:5000/core/property/?deal_id=d_123"

# Filter by tag
curl "http://localhost:5000/core/property/?tag=residential"
```

### Get Property Details
```bash
curl "http://localhost:5000/core/property/prop_abc123"
```

### Neighborhood Rating
```bash
curl -X POST http://localhost:5000/core/property/neighborhood_rating \
  -H "Content-Type: application/json" \
  -d '{
    "country": "CA",
    "region": "ON",
    "city": "Toronto",
    "address": "123 Main St",
    "postal": "M5H 2N2",
    "notes": "Downtown core"
  }'

# Response:
{
  "score": 0.64,
  "band": "B",
  "reasons": [
    "placeholder rating (no external data yet)",
    "CA model baseline",
    "region ON slightly higher baseline",
    "city provided (+signal)",
    "postal/zip provided (+signal)"
  ],
  "placeholders": true
}

# Bands:
# A: 0.75+  (Top tier)
# B: 0.55-0.75 (Good)
# C: 0.40-0.55 (Moderate)
# D: <0.40  (Lower)
```

### Get Comps (Placeholder)
```bash
curl -X POST http://localhost:5000/core/property/comps \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": "prop_abc123",
    "payload": {
      "beds": 3,
      "baths": 2,
      "sqft": 1800
    }
  }'

# Response:
{
  "placeholders": true,
  "suggested_arv": null,
  "comps": [],
  "notes": [
    "comps placeholder: provide your own comps list later",
    "future: integrate MLS/PropStream/HouseSigma/Realtor/Zillow sources via connectors"
  ]
}

# Ready for future integration with:
# - MLS (Canada/US)
# - PropStream
# - HouseSigma
# - Realtor.ca
# - Zillow
```

### Get Rent/Repair Estimates (Placeholder)
```bash
curl -X POST http://localhost:5000/core/property/rent_repairs \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": "prop_abc123",
    "payload": {
      "country": "CA",
      "beds": 3,
      "baths": 2,
      "sqft": 1800
    }
  }'

# Response:
{
  "placeholders": true,
  "suggested_rent": null,
  "repair_range": {
    "low": null,
    "high": null,
    "currency": "CAD"
  },
  "notes": [
    "rent/repairs placeholder: provide rent comps + repair line-items later",
    "future: integrate rentometer/market sources and your repair calculator packs"
  ]
}

# Ready for future integration with:
# - Rentometer
# - MarketRent
# - Local market data
# - Repair cost calculators
```

---

## Data Models Quick Reference

### Comms Models
- **Channel:** "sms" | "email" | "call" | "dm" | "letter"
- **Status:** "draft" | "ready" | "sent" | "failed" | "archived"

### JV Models
- **PartnerType:** "buyer" | "lender" | "jv" | "vendor" | "agent" | "other"
- **PartnerStatus:** "active" | "paused" | "blocked"

### Property Models
- **Country:** "CA" | "US"
- **Region:** Province codes (ON, BC, MB, etc.) or State codes (FL, TX, CA, etc.)

---

## Error Handling

All three modules use standard HTTP status codes:

- `200/201` - Success
- `400` - Bad request (validation error, missing required field)
- `404` - Not found (resource doesn't exist)
- `500` - Server error

Example error response:
```json
{
  "detail": "draft not found"
}
```

---

## Integration Points

### Comms → Existing
- Optional mirror to contact_log (non-breaking)
- References: deal_id, contact_id, buyer_id from deals

### JV → Existing
- Optional deal stats from deals module
- Links to any deal_id

### Property → Existing
- Standalone (references deal_id for linking)
- Ready for future comps/rent/repair integrators

---

## File Structure

```
backend/data/
├── comms/
│   ├── drafts.json        # Draft messages
│   └── sendlog.json       # Send history
├── jv/
│   ├── partners.json      # Partner registry
│   └── links.json         # Deal links
└── property/
    └── properties.json    # Property records
```

All files auto-create on first write with UTC ISO timestamps.
