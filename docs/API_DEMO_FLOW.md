# Sprint 3: Complete API Demo Flow

This document shows step-by-step how to use the Valhalla system for a complete deal pipeline including lead capture, buyer matching, and dashboard visibility.

## Prerequisites

- Valhalla API running on `http://localhost:4000`
- API Key: Set `X-API-Key` header (or use `test-builder-key` for local testing)
- Database initialized via `db_bootstrap.py`

## Full Pipeline Demo (Copy & Paste Ready)

Replace `http://localhost:4000` with your actual API base URL and `test-builder-key` with your actual API key.

---

### Step 1: Create a Lead

A lead represents an incoming seller or deal source.

```bash
curl -X POST http://localhost:4000/api/leads \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe Seller",
    "email": "john@example.com",
    "phone": "555-0001",
    "property_city": "Denver",
    "property_state": "CO",
    "property_zip": "80202",
    "estimated_arv": 450000.00,
    "source": "cold_call",
    "status": "qualified"
  }'
```

**Response includes:** `lead_id`, `created_at`, `status`

Save the `lead_id` for use in next step.

---

### Step 2: Create a Deal

A deal is the actionable opportunity derived from a lead.

```bash
curl -X POST http://localhost:4000/api/deals \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Downtown Denver SFH",
    "region": "Denver, CO",
    "property_type": "SFH",
    "price": 350000.00,
    "beds": 3,
    "baths": 2.0,
    "notes": "Foundation issues, needs 60k repair",
    "status": "active"
  }'
```

**Response includes:** `deal_id`, `headline`, `status`, `created_at`

Save the `deal_id` for matching and dashboard queries.

---

### Step 3: Update Deal Score

Indicate how strong the deal fundamentals are (0-100).

```bash
curl -X PUT http://localhost:4000/api/deals/{deal_id}/score \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 78.5,
    "reason": "Good ROI, quick rehab"
  }'
```

---

### Step 4: Advance Deal Stage

Move the deal through its lifecycle: `lead_received` → `preliminary_analysis` → `offer_ready` → `under_contract` → `closed`

```bash
curl -X POST http://localhost:4000/api/deals/{deal_id}/advance-stage \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "new_stage": "preliminary_analysis"
  }'
```

This automatically logs an audit event showing the stage transition.

---

### Step 5: Create an Offer

The proposed financial terms to the seller.

```bash
curl -X POST http://localhost:4000/api/offers \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": {deal_id},
    "offer_price": 280000.00,
    "emd_amount": 5000.00,
    "closing_window_days": 45,
    "conditions_summary": "As-is, 30-day close, subject to inspection",
    "generated_by": "API_Demo",
    "status": "draft"
  }'
```

**Response includes:** `offer_id`, `offer_price`, `status`

---

### Step 6: Create a Contract

Link the deal and offer to a legal contract document.

```bash
curl -X POST http://localhost:4000/api/contracts \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": {deal_id},
    "offer_id": {offer_id},
    "status": "draft",
    "template_id": "purchase_agreement_v1",
    "content": "This is the purchase agreement terms...",
    "pdf_url": "s3://contracts/deal_{deal_id}_contract.pdf"
  }'
```

---

### Step 7: Create a Buyer Profile

Register a cash buyer or investor looking for deals.

```bash
curl -X POST http://localhost:4000/api/buyers \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Midwest Investments LLC",
    "email": "deals@midwestinv.com",
    "phone": "555-9999",
    "regions": "Denver, Boulder, Fort Collins, Colorado",
    "property_types": "SFH,Duplex,Triplex",
    "min_price": 250000.00,
    "max_price": 500000.00,
    "min_beds": 2,
    "min_baths": 1.0,
    "tags": "cash-ready,30-day-close,rehab-experience",
    "active": true
  }'
```

**Response includes:** `buyer_id`, `name`, `active` status

---

### Step 8: List All Buyers

See all registered buyers in the system.

```bash
curl -X GET "http://localhost:4000/api/buyers?active=true" \
  -H "X-API-Key: test-builder-key"
```

**Response:** Array of buyer profiles. Each has:
- `id`, `name`, `email`, `phone`
- `regions`, `property_types`
- `min_price`, `max_price`, `min_beds`, `min_baths`
- `created_at`, `updated_at`

---

### Step 9: Get Specific Buyer

Retrieve a single buyer's full profile.

```bash
curl -X GET http://localhost:4000/api/buyers/{buyer_id} \
  -H "X-API-Key: test-builder-key"
```

---

### Step 10: Match Buyer to Deal

Find the best buyer match(es) for a specific deal. This scoring algorithm checks:
- Regional alignment (fuzzy match)
- Property type match
- Price range compatibility
- Bed/bath requirements
- Any buyer tags vs deal headline

```bash
curl -X POST http://localhost:4000/api/buyers/match/{deal_id} \
  -H "X-API-Key: test-builder-key"
```

**Response includes:**
```json
{
  "mode": "deal->buyers",
  "total": 3,
  "hits": [
    {
      "buyer_id": 1,
      "buyer_name": "Midwest Investments LLC",
      "score": 0.92,
      "reasons": ["region≈Denver (0.95)", "type=SFH", "price in range", "beds ok", "baths ok"]
    },
    {
      "buyer_id": 2,
      "buyer_name": "Rocky Mountain Capital",
      "score": 0.78,
      "reasons": ["region≈Denver (0.85)", "price near range"]
    }
  ]
}
```

The `score` ranges from 0 to 1. Top match should be presented to the buyer first.

---

### Step 11: View Dashboard Pipeline

Get a real-time operational dashboard showing all active deals and their status.

```bash
curl -X GET http://localhost:4000/api/dashboard/pipeline \
  -H "X-API-Key: test-builder-key"
```

**Response includes:**
```json
{
  "total_deals": 5,
  "deals": [
    {
      "deal_id": 1,
      "title": "Downtown Denver SFH",
      "stage": "preliminary_analysis",
      "score": 78.5,
      "contract_status": "pending",
      "buyer_status": "matched",
      "last_updated": "2026-03-26T14:30:00Z"
    }
  ]
}
```

Use this for operational visibility into the pipeline.

---

### Step 12: View Deal Timeline

Get the complete audit trail for a specific deal showing all actions and stage changes.

```bash
curl -X GET http://localhost:4000/api/dashboard/deals/{deal_id}/timeline \
  -H "X-API-Key: test-builder-key"
```

**Response includes:**
```json
{
  "deal_id": 1,
  "deal_title": "Downtown Denver SFH",
  "events": [
    {
      "timestamp": "2026-03-26T14:32:15Z",
      "action": "deal_buyer_match",
      "actor": "system",
      "target": "deal_1",
      "result": "success",
      "meta": {
        "deal_id": 1,
        "total_matches": 3,
        "top_buyer_id": 1
      }
    },
    {
      "timestamp": "2026-03-26T14:30:00Z",
      "action": "deal_created",
      "actor": "system",
      "target": "deal_1",
      "result": "success"
    }
  ]
}
```

---

### Step 13: Get Deal Audit Trail

Get all audit events for a specific deal (alternative endpoint to timeline).

```bash
curl -X GET http://localhost:4000/api/audit/deals/{deal_id} \
  -H "X-API-Key: test-builder-key"
```

**Response:** Array of audit events, newest first. Same format as timeline.

---

## Running the Full Demo

Create a script file `demo.sh`:

```bash
#!/bin/bash

API="http://localhost:4000"
KEY="test-builder-key"

echo "=== CREATING LEAD ==="
LEAD=$(curl -s -X POST $API/api/leads \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"name":"Test Seller","email":"test@example.com","phone":"555-1234","property_city":"Denver","property_state":"CO","estimated_arv":400000,"source":"API","status":"qualified"}')
echo $LEAD | jq .
LEAD_ID=$(echo $LEAD | jq -r '.lead_id // .id')

echo -e "\n=== CREATING DEAL ==="
DEAL=$(curl -s -X POST $API/api/deals \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"headline":"Test Deal","region":"Denver","property_type":"SFH","price":350000,"beds":3,"baths":2,"status":"active"}')
echo $DEAL | jq .
DEAL_ID=$(echo $DEAL | jq -r '.deal_id // .id')

echo -e "\n=== CREATING BUYER ==="
BUYER=$(curl -s -X POST $API/api/buyers \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"name":"Test Buyer","email":"buyer@test.com","regions":"Denver","property_types":"SFH","min_price":250000,"max_price":500000,"active":true}')
echo $BUYER | jq .
BUYER_ID=$(echo $BUYER | jq -r '.buyer_id // .id')

echo -e "\n=== MATCHING BUYER TO DEAL ==="
MATCH=$(curl -s -X POST $API/api/buyers/match/$DEAL_ID \
  -H "X-API-Key: $KEY")
echo $MATCH | jq .

echo -e "\n=== DASHBOARD PIPELINE ==="
curl -s -X GET $API/api/dashboard/pipeline \
  -H "X-API-Key: $KEY" | jq .

echo -e "\n=== DEAL TIMELINE ==="
curl -s -X GET $API/api/dashboard/deals/$DEAL_ID/timeline \
  -H "X-API-Key: $KEY" | jq .

echo -e "\n✅ DEMO COMPLETE"
```

Run it:
```bash
chmod +x demo.sh
./demo.sh
```

---

## Expected Results

If the system is working correctly, you should see:

1. ✅ Lead created in database (persists across restarts)
2. ✅ Deal created and linked to lead
3. ✅ Buyer created with preferences
4. ✅ Match score > 0 when buyer preferences align with deal
5. ✅ Dashboard shows the deal in pipeline
6. ✅ Timeline shows audit events for all actions
7. ✅ All data is persistent (survives app restart)

## Troubleshooting

**401 Unauthorized**: Check API key in `X-API-Key` header

**404 Not Found**: Endpoint not registered. Check that routers are imported in `main.py`

**500 Internal Error**: Check database connection and that `db_bootstrap.py` was run

**Empty results**: Verify API key has permission and data was created successfully (check audit logs)

---

## Next: Heimdall Activation

Once this flow works end-to-end, the system is ready for Heimdall (automated decision and orchestration layer) activation.
