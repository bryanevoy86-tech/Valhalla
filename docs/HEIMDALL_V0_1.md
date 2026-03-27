# HEIMDALL V0.1

**Release Date:** March 26, 2026  
**Version:** 0.1 (Operator-Assist Layer)  
**Status:** Operational  
**Classification:** Safe, Auditable, Operator-Controlled

---

## EXECUTIVE SUMMARY

Heimdall v0.1 is a practical, bounded operator-assist layer that makes the Valhalla core pipeline **controllable and understandable**.

Heimdall is **NOT** an autonomous system. It is not an AI. It is **not** empire control.

Heimdall is a safe, transparent tool that:
- ✅ Analyzes deals proactively
- ✅ Identifies blockers clearly
- ✅ Recommends next steps intelligently  
- ✅ Executes stage changes only with explicit approval
- ✅ Logs everything for audit
- ✅ Knows its limitations

---

## WHAT HEIMDALL DOES

### Analysis
```
POST /api/heimdall/deals/{deal_id}/analyze

Returns:
- Current deal state (arv, repairs, offer, contract, buyer match)
- Missing fields for next stage
- Blocker flags (what prevents advancement)
- Risk flags (warnings that don't block)
- Recommended next stage
- Plain-English explanation

No side effects - read-only.
```

### Recommendation
```
Same as Analysis - recommends next valid stage transition.

Example:
- "Next valid stage: offer_ready. Reason: data complete, no blockers."
- "Cannot advance: missing offer. Create offer, then try again."
```

### Controlled Advancement
```
POST /api/heimdall/deals/{deal_id}/advance-stage

Requires:
- Target stage
- approved_by (who authorizes)
- reason (why this advancement)
- override_reason (optional, if proceeding despite blockers)

Returns:
- Success or rejection
- Audit trail references
- Detailed explanation

All changes logged.
```

---

## WHAT HEIMDALL DOES NOT DO

### ❌ Explicitly Forbidden in v0.1

- **Send emails** - No notifications
- **Sign contracts** - No DocuSign integration
- **Process payments** - No Stripe/payment logic
- **Modify buyers** - Can observe, cannot change
- **Make autonomous decisions** - Always requires approval
- **Trigger cascading workflows** - Single-step only
- **Call external APIs** - Hermetically sealed
- **Fabricate data** - Uses only DB state + rules
- **Bypass stage rules** - Rules enforced, overrides logged

### ❌ Not Implemented (Won't Be in v0.1)

- Multi-deal workflows
- Predictive scoring
- AI integration
- Scheduled automation
- Event-driven triggering
- User role management
- Performance optimization

---

## ENDPOINTS

### Analyze
```
POST /api/heimdall/deals/{deal_id}/analyze

Input: (empty)
Output: DealAnalysis (full state + recommendations)

Example:
curl -X POST http://localhost:4000/api/heimdall/deals/1/analyze \
  -H "X-API-Key: test-builder-key"
```

### Advance Stage
```
POST /api/heimdall/deals/{deal_id}/advance-stage

Input: {
  "requested_stage": "offer_ready",
  "approved_by": "operator@company.com",
  "reason": "Offer ready to send",
  "override_reason": null  // optional
}

Output: {
  "deal_id": 1,
  "previous_stage": "preliminary_analysis",
  "new_stage": "offer_ready",
  "result": "success" or "rejected",
  "timestamp": "...",
  "audit_log_ids": [...]
}

Example:
curl -X POST http://localhost:4000/api/heimdall/deals/1/advance-stage \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "requested_stage": "offer_ready",
    "approved_by": "alice@company.com",
    "reason": "Data validated, ready to proceed"
  }'
```

---

## STAGE RULES

Heimdall enforces a deterministic stage machine:

```
draft → lead_received → preliminary_analysis → offer_ready → under_contract → closed
```

Valid transitions only. No skipping. No going backward.

For stage-specific requirements, see [HEIMDALL_STAGE_GUARDRAILS.md](HEIMDALL_STAGE_GUARDRAILS.md).

---

## BLOCKER DETECTION

Heimdall knows what's required for each stage:

| Stage | Requires | Blocks If Missing |
|-------|----------|------------------|
| lead_received | Lead data | (soft) |
| preliminary_analysis | ARV, repair estimate | arv, repairs missing |
| offer_ready | Offer created | no_offer |
| under_contract | Contract + content | no_contract, content_empty |
| closed | Contract signed | not_signed |

All blocking conditions are listed in analysis output.

---

## OVERRIDE MODEL

Operators can override blockers:

```
POST /api/heimdall/deals/1/advance-stage
{
  "requested_stage": "closed",
  "approved_by": "alice@company.com",
  "reason": "Closing deal",
  "override_reason": "Contract in external system, not in database yet"
}

Result:
- Stage advances
- Override logged to audit as override_used=true
- Override reason captured
- Audit shows both recommendation and override decision
```

---

## AUDIT MODEL

Every Heimdall action creates **separate, immutable audit entries**:

### 1. Analysis Log
```json
{
  "action": "heimdall_analyzed_deal",
  "actor": "Heimdall_v0.1",
  "deal_id": 1,
  "metadata": {
    "current_stage": "preliminary_analysis",
    "recommended_stage": "offer_ready",
    "blockers": [],
    "risks": ["no_buyer_match"]
  }
}
```

### 2. Advancement Log (if approved)
```json
{
  "action": "heimdall_stage_advanced",
  "actor": "Heimdall_v0.1",
  "deal_id": 1,
  "from_stage": "preliminary_analysis",
  "to_stage": "offer_ready",
  "metadata": {
    "approved_by": "alice@company.com",
    "reason": "Data complete",
    "override_used": false
  }
}
```

### 3. Rejection Log (if blocked)
```json
{
  "action": "heimdall_stage_advance_rejected",
  "actor": "Heimdall_v0.1",
  "deal_id": 1,
  "metadata": {
    "requested_stage": "closed",
    "blocker": "contract_not_signed",
    "override_available": true
  }
}
```

All queryable via `GET /api/audit/deals/{deal_id}`.

---

## SAFETY MODEL

Why Heimdall v0.1 is safe:

1. **Bounded scope** - Only modifies stage field, only with approval
2. **No external effects** - No emails, no APIs, no payments
3. **Immutable audit** - All decisions logged and cannot be deleted
4. **Operator-controlled** - Every action requires explicit approval
5. **Deterministic** - No fuzzy logic, no randomness
6. **Rule-enforced** - Stage rules are hard constraints
7. **Reversible** - Can be disabled/undeployed instantly
8. **No side channels** - No async, scheduled, or event-driven behavior

---

## KNOWN LIMITATIONS

1. **String-based stages** - Should be Python enum, but works
2. **Single-step operations** - Cannot do multi-step workflows
3. **Basic blocker logic** - Rules-based, not predictive
4. **No contract generation** - Only observes contract state
5. **No buyer automation** - Can see matches, cannot create
6. **Limited risk scoring** - Simple heuristics only
7. **No performance optimization** - Each analysis queries fresh
8. **No caching** - All reads are live from DB

These are intentional constraints for safety in v0.1.

---

## TESTING

Run the test suite:

```bash
pytest tests/test_heimdall_v0_1.py -v
```

Tests cover:
- ✅ Valid transitions
- ✅ Invalid transition rejection
- ✅ Blocker detection
- ✅ Override handling
- ✅ Audit logging
- ✅ Integration with pipeline

---

## API DEMO

See [HEIMDALL_API_DEMO_FLOW.md](HEIMDALL_API_DEMO_FLOW.md) for runnable curl examples.

Quick start:

```bash
# Analyze a deal
curl -X POST http://localhost:4000/api/heimdall/deals/1/analyze \
  -H "X-API-Key: test-builder-key"

# Advance stage (if analysis says you can)
curl -X POST http://localhost:4000/api/heimdall/deals/1/advance-stage \
  -H "X-API-Key: test-builder-key" \
  -H "Content-Type: application/json" \
  -d '{
    "requested_stage": "offer_ready",
    "approved_by": "you@company.com",
    "reason": "Ready to proceed"
  }'
```

---

## DEPLOYMENT

Heimdall is already deployed:

**Service:** `services/api/app/services/heimdall_service.py`  
**Router:** `services/api/app/routers/heimdall.py`  
**Registered in:** `services/api/app/main.py` (router registry)

To disable:
- Remove Heimdall from router registry in main.py
- Restart app
- Heimdall endpoints return 404

To enable:
- Ensure registrations are in place
- Restart app
- Endpoints available

---

## NEXT PHASES (Post-v0.1)

### Phase 2: Buyer Intelligence
- Automatic buyer matching on deal creation
- Buyer preference validation
- Match score explanations

### Phase 3: Contract Automation
- Automatic contract template selection
- Contract data population hints
- Signing status tracking and reminders

### Phase 4: Predictive Scoring
- Deal quality prediction
- Risk scoring based on historical data
- Repair cost estimation improvements

### Phase 5: Workflow Automation
- Multi-step workflows (with individual approvals)
- Scheduled reminders and checkpoints
- Integration with external systems

---

## CONFIGURATION

No configuration needed. Heimdall v0.1 works out of the box.

Optional tuning (future):
- Blocker severity levels
- Risk threshold tweaks
- Stage-specific rules customization

---

## SUPPORT

**Issues with Heimdall?**

1. Check test suite: `pytest tests/test_heimdall_v0_1.py`
2. Verify deal exists: `GET /api/deals/{id}`
3. Check audit trail: `GET /api/audit/deals/{id}`
4. Check logs for service errors

**Known issues:**
- (None in v0.1)

---

## PERMISSIONS

Heimdall uses same API key authentication as rest of system.

No role-based access control in v0.1 - all authenticated users can:
- Analyze any deal
- Advance any deal (with approval)
- See all audit trails

Future: Add role-based permissions.

---

## CONCLUSION

Heimdall v0.1 transforms the operational pipeline from "collection of endpoints" to "managed workflow."

It is:
- ✅ Safe (bounded, auditable, operator-controlled)
- ✅ Useful (makes blockers clear, recommends actions)
- ✅ Simple (single-step, deterministic)
- ✅ Transparent (everything logged)
- ✅ Ready (already deployed and tested)

Heimdall is not an AI. It is not autonomous. It is a tool for humans to manage Valhalla safely.

---

**Heimdall v0.1 is LIVE and OPERATIONAL.**

See [HEIMDALL_API_DEMO_FLOW.md](HEIMDALL_API_DEMO_FLOW.md) for hands-on demo.
