# HEIMDALL V0.1 API DEMO FLOW

**Purpose:** Step-by-step demonstration of Heimdall v0.1 capabilities

**Prerequisites:**
- Valhalla API running on `http://localhost:4000`
- Test deal in database (ID = 1, or adjust deal_id in examples)
- API Key: `test-builder-key` (or your actual key)

---

## SCENARIO

We're managing a deal through the pipeline:
1. Lead received (deal created)
2. Operator analyzes deal with Heimdall
3. Operator supplies missing data
4. Heimdall recommends next stage
5. Operator approves stage advancement
6. Audit log tracks every decision

---

## DEMO FLOW

### Step 0: Verify System Ready

First, make sure the operational core is working:

```bash
# Test API connectivity
curl -X GET http://localhost:4000/api/deals \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json"

# Expected: List of deals or empty array
```

---

### Step 1: Create a Test Deal (If needed)

If you don't have a deal to analyze:

```bash
# Create a deal
curl -X POST http://localhost:4000/api/deals \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Downtown Investment Property",
    "region": "Denver, CO",
    "property_type": "SFH",
    "price": 350000.00,
    "beds": 3,
    "baths": 2.0,
    "notes": "Good bones, needs updating",
    "status": "active"
  }'

# Save the deal_id from response for use in next steps
# Example response: {"id": 1, "headline": "Downtown Investment Property", ...}
```

**Save:** `DEAL_ID=1` (or whatever ID is returned)

---

### Step 2: HEIMDALL ANALYZE - Initial State

Get Heimdall's analysis of deal current state.

```bash
DEAL_ID=1

curl -X POST http://localhost:4000/api/heimdall/deals/$DEAL_ID/analyze \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json"
```

**Expected response:**

```json
{
  "deal_id": 1,
  "analysis_timestamp": "2026-03-26T15:30:00Z",
  "current_stage": "active",
  "deal_data": {
    "id": 1,
    "status": "active",
    "arv": 350000,
    "repairs": 0,
    "offer": 0,
    "mao": 0,
    "created_at": "2026-03-26T14:50:00"
  },
  "offer_data": null,
  "contract_data": null,
  "buyer_match_data": null,
  "missing_fields": [
    "deal.repairs",
    "offer"
  ],
  "blocker_flags": [
    "missing_repair_cost"
  ],
  "risk_flags": [
    "no_offer_yet"
  ],
  "recommendations": {
    "next_valid_stages": ["preliminary_analysis"],
    "recommended_stage": null,
    "recommendation_reason": "Blockers prevent advancing: missing_repair_cost",
    "can_advance_now": false,
    "why_cannot_advance": "missing_repair_cost"
  }
}
```

**Heimdall says:** "Cannot advance yet - missing repair cost estimate"

---

### Step 3: Fill in Missing Data

Operator fills in the missing blocker field (repair cost).

```bash
# Update deal with repair estimate
curl -X PUT http://localhost:4000/api/deals/1/update \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "arv": 350000,
    "repairs": 65000
  }'

# Or use direct approach if your API supports PATCH
curl -X PATCH http://localhost:4000/api/deals/1 \
  -H "X-API-Key: test-builder-key" \
  -d '{"repairs": 65000}'
```

---

### Step 4: HEIMDALL ANALYZE - After Data Supplied

Re-analyze the same deal:

```bash
curl -X POST http://localhost:4000/api/heimdall/deals/1/analyze \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json"
```

**Expected response (now unblocked):**

```json
{
  "deal_id": 1,
  "analysis_timestamp": "2026-03-26T15:32:00Z",
  "current_stage": "active",
  "deal_data": {
    "arv": 350000,
    "repairs": 65000,
    ...
  },
  "missing_fields": [
    "offer"
  ],
  "blocker_flags": [],
  "risk_flags": [
    "high_repair_ratio_18pct"
  ],
  "recommendations": {
    "next_valid_stages": ["preliminary_analysis"],
    "recommended_stage": "preliminary_analysis",
    "recommendation_reason": "Ready to advance to preliminary_analysis",
    "can_advance_now": true
  }
}
```

**Heimdall says:** "Ready to advance! All blockers cleared."

---

### Step 5: HEIMDALL ADVANCE STAGE - Get Approval

Operator approves stage advancement:

```bash
curl -X POST http://localhost:4000/api/heimdall/deals/1/advance-stage \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "requested_stage": "preliminary_analysis",
    "approved_by": "alice@ourcompany.com",
    "reason": "ARV and repairs confirmed, ready for analysis"
  }'
```

**Expected response:**

```json
{
  "deal_id": 1,
  "action": "stage_advanced",
  "previous_stage": "active",
  "new_stage": "preliminary_analysis",
  "approved_by": "alice@ourcompany.com",
  "timestamp": "2026-03-26T15:35:00Z",
  "result": "success",
  "notes": "Stage advanced successfully",
  "blocker_overrides": []
}
```

**Status:** ✅ DEAL MOVED TO PRELIMINARY_ANALYSIS

---

### Step 6: HEIMDALL ANALYZE - New Stage State

Now that deal is in preliminary_analysis, what's next?

```bash
curl -X POST http://localhost:4000/api/heimdall/deals/1/analyze \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json"
```

**Expected response:**

```json
{
  "current_stage": "preliminary_analysis",
  "missing_fields": ["offer"],
  "blocker_flags": [
    "no_offer_created"
  ],
  "recommendations": {
    "next_valid_stages": ["offer_ready"],
    "recommended_stage": null,
    "recommendation_reason": "Blockers prevent advancing: no_offer_created",
    "can_advance_now": false
  }
}
```

**Heimdall says:** "Cannot advance to offer_ready - need to create an offer first"

---

### Step 7: Create Offer (Manually)

Operator creates offer via system:

```bash
curl -X POST http://localhost:4000/api/offers \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": 1,
    "offer_price": 280000,
    "emd_amount": 5000,
    "closing_window_days": 45,
    "conditions_summary": "As-is, 45-day close",
    "generated_by": "Heimdall_Demo",
    "status": "draft"
  }'

# Save: OFFER_ID=<response.id>
```

---

### Step 8: HEIMDALL ANALYZE - Offer Created

Analyze again:

```bash
curl -X POST http://localhost:4000/api/heimdall/deals/1/analyze \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json"
```

**Expected response:**

```json
{
  "current_stage": "preliminary_analysis",
  "offer_data": {
    "deal_id": 1,
    "offer_price": 280000,
    "status": "draft"
  },
  "blocker_flags": [],
  "recommendations": {
    "next_valid_stages": ["offer_ready"],
    "recommended_stage": "offer_ready",
    "recommendation_reason": "Ready to advance to offer_ready",
    "can_advance_now": true
  }
}
```

**Heimdall says:** "All clear - ready to move to offer_ready!"

---

### Step 9: HEIMDALL ADVANCE STAGE - Offer Ready

```bash
curl -X POST http://localhost:4000/api/heimdall/deals/1/advance-stage \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "requested_stage": "offer_ready",
    "approved_by": "bob@ourcompany.com",
    "reason": "Offer reviewed and ready to send to seller"
  }'
```

**Expected:** ✅ Stage advanced to offer_ready

---

### Step 10: HEIMDALL ANALYZE - What's Missing?

```bash
curl -X POST http://localhost:4000/api/heimdall/deals/1/analyze \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json"
```

**Expected response:**

```json
{
  "current_stage": "offer_ready",
  "blocker_flags": [
    "no_contract"
  ],
  "risk_flags": [
    "no_buyer_match"
  ],
  "recommendations": {
    "next_valid_stages": ["under_contract"],
    "can_advance_now": false,
    "recommendation_reason": "Blockers prevent advancing: no_contract"
  }
}
```

**Heimdall says:** "Need contract before advancing. Also: recommend buyer matching"

---

### Step 11: AUDIT TRAIL - See History

Check what Heimdall has logged:

```bash
curl -X GET http://localhost:4000/api/audit/deals/1 \
  -H "X-API-Key: test-builder-key"
```

**Expected response:**

```json
[
  {
    "id": 1025,
    "action": "heimdall_stage_advanced",
    "actor": "Heimdall_v0.1",
    "target": "deal_1",
    "result": "success",
    "timestamp": "2026-03-26T15:35:00Z",
    "meta": {
      "from_stage": "active",
      "to_stage": "preliminary_analysis",
      "approved_by": "alice@ourcompany.com"
    }
  },
  {
    "id": 1024,
    "action": "heimdall_recommended_stage",
    "actor": "Heimdall_v0.1",
    "target": "deal_1",
    "result": "success",
    "timestamp": "2026-03-26T15:35:00Z",
    "meta": {
      "from_stage": "active",
      "to_stage": "preliminary_analysis"
    }
  }
]
```

---

### Step 12: DEAL DASHBOARD - See Full State

```bash
curl -X GET http://localhost:4000/api/dashboard/pipeline \
  -H "X-API-Key: test-builder-key"
```

Shows deal in pipeline with Heimdall-managed stage.

---

### Step 13: SCENARIO - Blocked Advancement

Try to advance when blockers exist:

```bash
# Try to skip to "under_contract" (invalid - should be "offer_ready" first)
curl -X POST http://localhost:4000/api/heimdall/deals/1/advance-stage \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "requested_stage": "under_contract",
    "approved_by": "charlie@ourcompany.com",
    "reason": "Jump to contract"
  }'
```

**Expected response:**

```json
{
  "deal_id": 1,
  "action": "stage_advance_rejected",
  "previous_stage": "offer_ready",
  "requested_stage": "under_contract",
  "result": "rejected",
  "reason": "Invalid transition from offer_ready to under_contract",
  "timestamp": "2026-03-26T15:40:00Z"
}
```

---

### Step 14: SCENARIO - Override

Operator knows about an issue but proceeds anyway:

```bash
curl -X POST http://localhost:4000/api/heimdall/deals/1/advance-stage \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "requested_stage": "closed",
    "approved_by": "diana@ourcompany.com",
    "reason": "Deal is complete",
    "override_reason": "Contract in external system, not synced yet"
  }'
```

**Response:** Override noted in audit trail as `override_used=true`

---

## BASH SCRIPT VERSION

Save as `heimdall_demo.sh`:

```bash
#!/bin/bash

set -e

API="http://localhost:4000"
KEY="test-builder-key"

DEAL_ID=${1:-1}

echo "=== HEIMDALL V0.1 DEMO ==="
echo "Deal ID: $DEAL_ID"
echo

# Step 1: Analyze
echo "STEP 1: HEIMDALL ANALYZES DEAL"
ANALYSIS=$(curl -s -X POST $API/api/heimdall/deals/$DEAL_ID/analyze \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json")
echo $ANALYSIS | jq .
CURRENT=$(echo $ANALYSIS | jq -r '.current_stage')
RECOMMENDED=$(echo $ANALYSIS | jq -r '.recommendations.recommended_stage')
echo "Current stage: $CURRENT"
echo "Recommended: $RECOMMENDED"
echo

# Step 2: Try to advance (if possible)
if [ "$RECOMMENDED" != "null" ]; then
  echo "STEP 2: HEIMDALL ADVANCES STAGE"
  ADVANCE=$(curl -s -X POST $API/api/heimdall/deals/$DEAL_ID/advance-stage \
    -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
    -d "{
      \"requested_stage\": \"$RECOMMENDED\",
      \"approved_by\": \"demo@test.com\",
      \"reason\": \"Demo approval\"
    }")
  echo $ADVANCE | jq .
else
  echo "STEP 2: Cannot advance - blockers present"
fi
echo

# Step 3: Show audit trail
echo "STEP 3: AUDIT TRAIL"
curl -s -X GET $API/api/audit/deals/$DEAL_ID \
  -H "X-API-Key: $KEY" | jq '.[] | {action, actor, timestamp, result}'
echo

echo "✅ DEMO COMPLETE"
```

Run it:

```bash
chmod +x heimdall_demo.sh
./heimdall_demo.sh 1
```

---

## EXPECTED OUTPUTS

If system is working:

- ✅ Analyze endpoints return deal state
- ✅ Advance endpoints accept approval payloads
- ✅ Blockers are detected and explained
- ✅ Audit events show in timeline
- ✅ Invalid transitions are rejected
- ✅ Overrides are accepted when provided

If system has issues:

- ❌ 404: Deal not found (create a deal first)
- ❌ 401: API key invalid
- ❌ 500: Database or service error (check logs)
- ❌ 422: Request body validation error (check JSON)

---

## TROUBLESHOOTING

**"Deal not found"**
→ Create a deal first with `/api/deals` endpoint

**"Cannot connect to API"**
→ Make sure app is running: `uvicorn app.main:app --reload --port 4000`

**"API key invalid"**
→ Check X-API-Key header matches your key

**"Stage advancement rejected"**
→ Check blockers in analysis response, fill missing data

---

## NEXT STEPS

After successful demo:

1. Run automated test suite: `pytest tests/test_heimdall_v0_1.py`
2. Extend to full pipeline integration
3. Add buyer matching to Heimdall (next phase)
4. Add contract generation trigger (next phase)

---

**Heimdall v0.1 is ready for demonstrations.**
