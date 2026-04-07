# VALHALLA BACKEND DRY-RUN CHECKLIST

**Date**: April 6, 2026  
**Purpose**: Prove end-to-end system functionality before WeWeb integration  
**Scope**: Legal, Finance, Compliance layers - no new architecture  

---

## PHASE 0: CONFIGURATION

### Step 0.1: Legal Contacts Registry

Populate with test contacts:

```bash
curl -X POST http://localhost:4000/api/legal/registry/update-region \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Valhalla Legacy Inc.",
    "region_code": "MB",
    "lawyer_email": "lawyer@example.com",
    "accountant_email": "accountant@example.com",
    "title_company": "Example Title Co.",
    "title_company_email": "title@example.com",
    "cc": ["ops@example.com"]
  }'
```

**Expected**: Registry updated successfully

### Step 0.2: SMTP Configuration (Optional - For Email Testing)

Set environment variables:

```bash
export LEGAL_SENDER_EMAIL="noreply@valhalla.local"
export LEGAL_SMTP_HOST="localhost"
export LEGAL_SMTP_PORT="1025"
export LEGAL_SMTP_USERNAME="test"
export LEGAL_SMTP_PASSWORD="test"
export LEGAL_SMTP_USE_TLS="false"
```

**Note**: Can skip if no email server available - system will handle gracefully

---

## PHASE 1: BACKEND STARTUP

### Step 1.1: Start Backend Server

```bash
cd d:\dev\services\api
uvicorn app.main:app --reload --port 4000
```

**Expected Output**:
```
INFO:     Uvicorn running on http://127.0.0.1:4000
INFO:     Application startup complete
```

**Wait For**: "startup complete" message before proceeding

### Step 1.2: Verify Server Running

```bash
curl http://localhost:4000/health
```

**Expected**: 
```json
{
  "status": "healthy"
}
```

---

## PHASE 2: SANITY CHECKS

Run these in order. All should return 200 with valid data:

### Check 2.1: Compliance Mode

```bash
curl http://localhost:4000/api/compliance/mode
```

**Expected**:
```json
{
  "mode": "EIA_PROTECTED",
  "eia_mode_active": true,
  "personal_draws_allowed": false,
  ...
}
```

**✓ Pass If**: Mode is EIA_PROTECTED

### Check 2.2: Legal Templates

```bash
curl http://localhost:4000/api/legal/templates
```

**Expected**: Array of 8 templates:
- purchase_sale_agreement
- assignment_of_contract
- buyer_non_circumvention
- seller_disclosure
- earnest_money_receipt
- jv_partnership_agreement
- terms_of_service
- privacy_policy

**✓ Pass If**: All 8 templates present

### Check 2.3: Finance Summary

```bash
curl http://localhost:4000/api/finance/status/summary
```

**Expected**:
```json
{
  "total_items": 0,
  "pending": 0,
  "approved": 0,
  "blocked": 0
}
```

**✓ Pass If**: Structure present (counts may vary)

### Check 2.4: Legal Summary

```bash
curl http://localhost:4000/api/legal/status/summary
```

**Expected**:
```json
{
  "total_documents": 0,
  "queued_pending_approval": 0,
  "approved_pending_send": 0,
  "sent": 0
}
```

**✓ Pass If**: Structure present

---

## PHASE 3: LEGAL WORKFLOW DRY RUN

### Step 3.1: Trigger Legal Package from Deal Stage

```bash
curl -X POST http://localhost:4000/api/legal/trigger-package-from-stage \
  -H "Content-Type: application/json" \
  -d '{
    "stage": "deal_ready_for_offer",
    "deal": {
      "deal_id": "DEAL-DRYRUN-001",
      "seller_name": "John Seller",
      "buyer_name": "Valhalla Legacy Inc.",
      "your_company": "Valhalla Legacy Inc.",
      "property_address": "123 Main St, Winnipeg, MB",
      "purchase_price": "185000",
      "earnest_money": "2500",
      "title_company": "Example Title Co.",
      "inspection_days": 10,
      "closing_date": "2026-04-30",
      "additional_terms": "Dry run only. Subject to lawyer review.",
      "region_code": "MB",
      "deal_type": "wholesale"
    }
  }'
```

**Expected**:
```json
{
  "triggered": true,
  "package_id": "DEAL-DRYRUN-001__deal_ready_for_offer",
  "documents_queued": 3,
  "total": 3,
  "sent": 0,
  "approved": 0,
  "pending": 3
}
```

**✓ Pass If**: 
- triggered = true
- documents_queued = 3
- pending = 3
- No "reason" field (error indicator)

**Save Response**: Copy full response to `DRYRUN_legal_package_response.json`

### Step 3.2: Check Legal Status Feed

```bash
curl http://localhost:4000/api/legal/status/feed
```

**Expected**:
```json
{
  "summary": {
    "total_documents": 3,
    "queued_pending_approval": 3,
    "approved_pending_send": 0,
    "sent": 0
  },
  "items": [
    {
      "approval_id": "DEAL-DRYRUN-001__deal_ready_for_offer__...",
      "template_key": "...",
      "status": "queued_pending_approval",
      ...
    },
    ...
  ]
}
```

**✓ Pass If**:
- total_documents = 3
- queued_pending_approval = 3
- items array has 3 entries
- All statuses are "queued_pending_approval"

### Step 3.3: Check Legal Package History

```bash
curl http://localhost:4000/api/legal/status/packages
```

**Expected**:
```json
{
  "package_count": 1,
  "packages": [
    {
      "package_id": "DEAL-DRYRUN-001__deal_ready_for_offer",
      "document_count": 3,
      "sent_count": 0,
      "approved_count": 0,
      "pending_count": 3,
      ...
    }
  ]
}
```

**✓ Pass If**:
- package_count = 1
- document_count = 3
- pending_count = 3

### Step 3.4: Check Legal Audit Trail

```bash
curl http://localhost:4000/api/legal/status/audit
```

**Expected**: Recent events including:
- Multiple "document_queued" events for DEAL-DRYRUN-001

**✓ Pass If**: Queued events visible

**Save File**: `cat services/api/app/legal/audit/legal_send_audit.jsonl > DRYRUN_legal_audit.jsonl`

### Step 3.5: Approve and Send Legal Package

```bash
curl -X POST http://localhost:4000/api/legal/approve-and-send-package \
  -H "Content-Type: application/json" \
  -d '{
    "stage": "deal_ready_for_offer",
    "deal_id": "DEAL-DRYRUN-001"
  }'
```

**Expected**:
```json
{
  "package_sent": true,
  "stage": "deal_ready_for_offer",
  "deal_id": "DEAL-DRYRUN-001",
  "approved_count": 3,
  "sent_count": 3,
  "total_count": 3,
  "results": [...]
}
```

**✓ Pass If**:
- package_sent = true
- approved_count = 3
- sent_count = 3

**Note**: If SMTP not configured, will still approve but "sent" may show warning (acceptable)

### Step 3.6: Verify Legal Status Updated

```bash
curl http://localhost:4000/api/legal/status/feed
```

**Expected**: 
- status changed to "sent" or "approved_pending_send"
- approved_pending_send or sent counts > 0

**✓ Pass If**: Documents no longer pending

---

## PHASE 4: FINANCE WORKFLOW DRY RUN

### Step 4.1: Build Financial Package

```bash
curl -X POST http://localhost:4000/api/finance/package/build \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": "DEAL-DRYRUN-001",
    "purchase_price": 185000,
    "assignment_fee": 10000,
    "earnest_money": 2500,
    "closing_costs": 1500,
    "requested_by": "heimdall"
  }'
```

**Expected**:
```json
{
  "package_id": "DEAL-DRYRUN-001__finance_package",
  "deal_id": "DEAL-DRYRUN-001",
  "triggered": true,
  "ledger": {
    "deal_id": "DEAL-DRYRUN-001",
    "purchase_price": 185000,
    "assignment_fee": 10000,
    "earnest_money": 2500,
    "closing_costs": 1500,
    "profit_expected": 8500,
    ...
  },
  "disbursement_count": 3,
  "queued_count": 3,
  "blocked_count": 0,
  "intents": [
    {
      "payer": "buyer",
      "payee": "title_company",
      "amount": 2500,
      "purpose": "earnest_money",
      ...
    },
    ...
  ]
}
```

**✓ Pass If**:
- triggered = true
- ledger.profit_expected = 8500 (10000 - 1500)
- disbursement_count = 3
- queued_count = 3
- blocked_count = 0

**Save Response**: Copy to `DRYRUN_finance_package_response.json`

### Step 4.2: Check Finance Status

```bash
curl http://localhost:4000/api/finance/status/summary
```

**Expected**:
```json
{
  "total_items": 3,
  "pending": 3,
  "approved": 0,
  "blocked": 0
}
```

**✓ Pass If**: total_items = 3, pending = 3

### Step 4.3: Check Finance Package History

```bash
curl http://localhost:4000/api/finance/status/packages
```

**Expected**:
```json
{
  "package_count": 1,
  "packages": [
    {
      "package_id": "DEAL-DRYRUN-001__finance_package",
      "deal_id": "DEAL-DRYRUN-001",
      "intent_count": 3,
      "approved_count": 0,
      "blocked_count": 0,
      "pending_count": 3,
      ...
    }
  ]
}
```

**✓ Pass If**: intent_count = 3, pending_count = 3

### Step 4.4: Check Finance Audit

```bash
curl http://localhost:4000/api/finance/status/audit
```

**Expected**: Recent events including finance_intent_queued

**✓ Pass If**: Events visible

**Save File**: `cat services/api/app/finance/audit/finance_audit.jsonl > DRYRUN_finance_audit.jsonl`

### Step 4.5: Approve Finance Package

```bash
curl -X POST http://localhost:4000/api/finance/package/approve \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": "DEAL-DRYRUN-001",
    "deal_data": {
      "deal_id": "DEAL-DRYRUN-001",
      "purchase_price": 185000,
      "assignment_fee": 10000,
      "earnest_money": 2500,
      "closing_costs": 1500
    },
    "approver": "bryan"
  }'
```

**Expected**:
```json
{
  "package_approved": true,
  "deal_id": "DEAL-DRYRUN-001",
  "approved_count": 3,
  "failed_count": 0,
  "total_count": 3,
  "results": [...]
}
```

**✓ Pass If**:
- package_approved = true
- approved_count = 3
- failed_count = 0

### Step 4.6: Verify Finance Status Updated

```bash
curl http://localhost:4000/api/finance/status/summary
```

**Expected**: approved count > 0

**✓ Pass If**: Counts changed from pending to approved

---

## PHASE 5: EIA PROTECTION VERIFICATION

### Step 5.1: Try Blocked Personal Draw (Should Fail)

```bash
curl -X POST http://localhost:4000/api/finance/intent/queue \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": "DEAL-DRYRUN-001",
    "intent_id": "INTENT-PERSONAL-001",
    "amount": 500,
    "purpose": "owner_draw",
    "payee": "bryan",
    "requested_by": "heimdall"
  }'
```

**Expected**:
```json
{
  "queued": true,
  "blocked": true,
  "block_reason": "Personal draw or personal transfer blocked in EIA mode",
  "eia_restrictions": {
    "blocked": true,
    "reasons": ["Personal draw or personal transfer blocked in EIA mode"],
    "mode": "EIA_PROTECTED"
  }
}
```

**✓ Pass If**:
- blocked = true
- block_reason contains "EIA"
- eia_restrictions.blocked = true

**Save Response**: Copy to `DRYRUN_eia_blocked_personal_draw.json`

### Step 5.2: Verify Compliance Mode Still Active

```bash
curl http://localhost:4000/api/compliance/mode
```

**Expected**: eia_mode_active = true

**✓ Pass If**: Mode unchanged

---

## PHASE 6: FREEZE CONTROL VERIFICATION

### Step 6.1: Freeze Finance System

```bash
curl -X POST http://localhost:4000/api/finance/freeze \
  -H "Content-Type: application/json" \
  -d '{
    "frozen": true,
    "reason": "dry run freeze test"
  }'
```

**Expected**:
```json
{
  "frozen": true,
  "reason": "dry run freeze test"
}
```

**✓ Pass If**: frozen = true

### Step 6.2: Try to Queue Intent While Frozen (Should Fail)

```bash
curl -X POST http://localhost:4000/api/finance/intent/queue \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": "DEAL-DRYRUN-001",
    "intent_id": "INTENT-FROZEN-001",
    "amount": 1000,
    "purpose": "earnest_money",
    "payee": "title_company",
    "requested_by": "heimdall"
  }'
```

**Expected**:
```json
{
  "blocked": true,
  "block_reason": "Finance system frozen: dry run freeze test"
}
```

**✓ Pass If**:
- blocked = true
- Mentions "frozen"

**Save Response**: Copy to `DRYRUN_finance_freeze_blocked.json`

### Step 6.3: Unfreeze System

```bash
curl -X POST http://localhost:4000/api/finance/freeze \
  -H "Content-Type: application/json" \
  -d '{
    "frozen": false,
    "reason": null
  }'
```

**Expected**: frozen = false

**✓ Pass If**: System unfrozen

---

## PHASE 7: EIA EXIT VALIDATION TEST

### Step 7.1: Validate Exit Readiness (Test Only)

```bash
curl -X POST http://localhost:4000/api/compliance/eia/exit/validate \
  -H "Content-Type: application/json" \
  -d '{
    "audit_selfcheck_passed": true,
    "reserve_floor_met": true,
    "founder_approved": true,
    "accountant_review_ready": true,
    "updated_by": "bryan"
  }'
```

**Expected**:
```json
{
  "can_exit_eia_mode": true,
  "blocker_count": 0,
  "blockers": [],
  "checked_at": "2026-04-06T..."
}
```

**✓ Pass If**: can_exit_eia_mode = true

**⚠️ DO NOT EXECUTE NEXT STEP UNLESS YOU WANT TO ACTUALLY EXIT EIA MODE**

### Step 7.2: Test Incomplete Exit (Should Fail)

```bash
curl -X POST http://localhost:4000/api/compliance/eia/exit/validate \
  -H "Content-Type: application/json" \
  -d '{
    "audit_selfcheck_passed": false,
    "reserve_floor_met": false,
    "founder_approved": false,
    "accountant_review_ready": false,
    "updated_by": "bryan"
  }'
```

**Expected**:
```json
{
  "can_exit_eia_mode": false,
  "blocker_count": 4,
  "blockers": [
    "Audit self-check has not passed",
    "Reserve floor has not been met",
    ...
  ]
}
```

**✓ Pass If**: can_exit_eia_mode = false, blockers listed

---

## PHASE 8: FINAL VERIFICATION CHECKLIST

Run this checklist. All should be ✓:

- [ ] Backend starts without errors
- [ ] Health check returns 200
- [ ] Compliance mode shows EIA_PROTECTED
- [ ] Legal templates list loads (8 templates)
- [ ] Finance summary loads
- [ ] Legal package triggered successfully (3 docs)
- [ ] Legal documents queued and visible
- [ ] Legal package history shows 1 package
- [ ] Legal audit trail has queued events
- [ ] Legal package approved and sent
- [ ] Legal status updated to sent/approved
- [ ] Finance package built (ledger + 3 intents)
- [ ] Expected profit calculated correctly (8500)
- [ ] Finance intents queued and visible
- [ ] Finance package history shows 1 package
- [ ] Finance audit trail has queued events
- [ ] Finance package approved (all 3 intents)
- [ ] Finance status updated to approved
- [ ] EIA blocked personal draw attempt ✓
- [ ] Personal draw shows correct block reason
- [ ] Compliance mode still active
- [ ] Finance system froze successfully
- [ ] Frozen system blocked new intents
- [ ] Finance system unfroze successfully
- [ ] Exit validation recognizes requirements met
- [ ] Exit validation correctly blocks incomplete exit
- [ ] No syntax/runtime errors during entire run

---

## PHASE 9: SAVE REFERENCE ARTIFACTS

Keep copies of these for WeWeb wiring reference:

```bash
# Create dry-run results directory
mkdir -p services/api/DRYRUN_RESULTS

# Copy responses
cat > services/api/DRYRUN_RESULTS/legal_package_response.json << 'EOF'
[Paste Step 3.1 response here]
EOF

cat > services/api/DRYRUN_RESULTS/finance_package_response.json << 'EOF'
[Paste Step 4.1 response here]
EOF

cat > services/api/DRYRUN_RESULTS/eia_blocked_personal_draw.json << 'EOF'
[Paste Step 5.1 response here]
EOF

cat > services/api/DRYRUN_RESULTS/finance_freeze_blocked.json << 'EOF'
[Paste Step 6.2 response here]
EOF

# Copy audit files
cp services/api/app/legal/audit/legal_send_audit.jsonl services/api/DRYRUN_RESULTS/
cp services/api/app/finance/audit/finance_audit.jsonl services/api/DRYRUN_RESULTS/

# Copy compliance state
cp services/api/app/compliance/state/compliance_mode.json services/api/DRYRUN_RESULTS/
```

---

## PHASE 10: SUCCESS CRITERIA

✅ **DRY RUN PASSES IF:**

1. All phases 1-7 complete without errors
2. All endpoints respond with expected structures
3. Legal package: generated → approved → sent
4. Finance package: built → queued → approved
5. EIA blocks personal transfers correctly
6. Freeze blocks intents correctly
7. Exit validation logic works
8. Audit trails record all events
9. Compliance mode stable throughout

✅ **THEN:**

Backend is **PROVEN**, **CONFIGURED**, **FROZEN**

Do NOT add more features until WeWeb tokens arrive.

---

## PHASE 11: TROUBLESHOOTING

### Issue: Port 4000 in use

```bash
# Find process on port 4000
netstat -ano | findstr :4000
# Kill process (replace PID)
taskkill /PID [PID] /F
```

### Issue: Module not found

Ensure virtual environment is activated:
```bash
d:\dev\.venv\Scripts\activate
```

### Issue: Templates not loading

Check path:
```bash
ls services/api/app/legal/templates/
```

Should contain 8 JSON files.

### Issue: SMTP errors

Either:
1. Set valid SMTP env vars, OR
2. Accept graceful SMTP failure (documented in code)

System should not crash either way.

### Issue: Compliance mode errors

Check file exists:
```bash
ls services/api/app/compliance/state/compliance_mode.json
```

Should auto-create on first run.

---

## COMPLETION

When all checks pass:

1. Screenshot or document full test run
2. Save artifacts to DRYRUN_RESULTS/
3. Commit reference responses to version control
4. **STOP** - do not add features
5. **WAIT** for WeWeb tokens
6. **THEN** wire frontend to proven backend

---

**DRY RUN DOCUMENT VERSION**: 1.0  
**LAST UPDATED**: April 6, 2026  
**STATUS**: Ready for testing
