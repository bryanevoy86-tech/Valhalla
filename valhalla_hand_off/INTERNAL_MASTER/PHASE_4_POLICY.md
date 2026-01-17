# PHASE 4 POLICY DEFINITION
**Real Data Outbound Mode - Safe Gate Checklist**

Last Updated: 2026-01-08
Status: **READY FOR PHASE 4 TRANSITION**

---

## Executive Summary

Phase 4 represents the **transition from sandbox (DRY-RUN) to production (LIVE)**, with real data flowing to real systems. This policy defines non-negotiable safety gates, allowed actions, and hard caps to prevent institutional risk.

**Key Principle**: "Phase 4 is not 'turn it on.' It is 'turn on ONE small thing safely.'"

---

## 1. PHASE 4 GATE CHECKLIST (9 Critical Items)

Before transitioning from Phase 3 to Phase 4:

### ☐ Gate 1: Guard Module Removal Authorization
- [ ] Legal/Compliance has signed off on removing Phase 3 safety guard
- [ ] Audit trail documented with approval date and signer
- [ ] Rollback procedure documented (if needed)
- **Non-negotiable**: No removal without documented approval

### ☐ Gate 2: Real Outbound Integration Tested
- [ ] Lead export API endpoint verified (POST /api/leads)
- [ ] Authentication token refreshing tested (no expiry during batch)
- [ ] Error handling for failed outbound requests confirmed
- [ ] Retry logic for transient failures validated
- **Non-negotiable**: Must handle 100% failure case (network down)

### ☐ Gate 3: Institutional Data Safety
- [ ] PII masking rules reviewed (email/phone redaction if needed)
- [ ] GDPR/data privacy checklist signed
- [ ] Lead deduplication tested (no duplicate sends to external system)
- [ ] Data retention policy documented
- **Non-negotiable**: No personal data leakage

### ☐ Gate 4: Load Limits Enforced
- [ ] VALHALLA_MAX_LEADS_PER_CYCLE hard-set (default: 25, max: 100)
- [ ] VALHALLA_MAX_ACTIONS_PER_CYCLE hard-set (default: 0 → Phase 4: 5)
- [ ] Rate limiting: max 5 requests/second (throttle enforced)
- [ ] Memory limits: sandbox process capped at 512MB
- **Non-negotiable**: No runaway batch exports

### ☐ Gate 5: Monitoring & Alerting Active
- [ ] Slack webhook configured for failures
- [ ] Email alerts to ops team (threshold: 5+ failures/hour)
- [ ] Dashboard shows real-time lead flow
- [ ] Rollback trigger defined (stop outbound if failure rate > 10%)
- **Non-negotiable**: No blind operations

### ☐ Gate 6: Financial Limits Confirmed
- [ ] Max daily leads: 10,000 (prevents overspending on processing)
- [ ] Max budget exposure: $50M (score * lead value cap)
- [ ] Cost per lead analysis: < $10 per lead to market
- [ ] ROI breakeven documented (must show positive 6-month ROI)
- **Non-negotiable**: Finance approval required

### ☐ Gate 7: Rollback Procedure Documented
- [ ] Rollback command: `VALHALLA_PHASE=3 python SANDBOX_ACTIVATION.py`
- [ ] Expected rollback time: < 5 minutes
- [ ] Data state after rollback: verified clean
- [ ] Tested rollback at least once with live data
- **Non-negotiable**: Must be able to stop and revert quickly

### ☐ Gate 8: Stakeholder Sign-Offs
- [ ] CEO/Leadership: Approved Phase 4 policy
- [ ] CFO: Approved financial limits and ROI
- [ ] General Counsel: Approved data/privacy compliance
- [ ] Risk Officer: Approved operational risks
- **Non-negotiable**: Executive sponsorship required

### ☐ Gate 9: 72-Hour Stability Test Passed
- [ ] Phase 3 ran for 72+ hours without interruption
- [ ] Export quality stable (score distributions, no data drift)
- [ ] No orphaned processes or memory leaks
- [ ] Guard module prevented all unsafe operations
- **Non-negotiable**: Must prove Phase 3 stability first

---

## 2. NON-NEGOTIABLE CONSTRAINTS (Phase 4)

These are **hard stops**—violating any means immediate rollback to Phase 3.

### Environment Variables (Read-Only)
```env
VALHALLA_PHASE=4                        # Phase 4 LIVE mode (cannot be changed without manual restart)
VALHALLA_REAL_DATA_INGEST=1             # Real data must be enabled
VALHALLA_DRY_RUN=0                      # DRY-RUN disabled in Phase 4 only
VALHALLA_DISABLE_OUTBOUND=0             # Outbound ENABLED in Phase 4
VALHALLA_MAX_LEADS_PER_CYCLE=25         # Hard limit: 25 leads/cycle (max 100)
VALHALLA_MAX_ACTIONS_PER_CYCLE=5        # Hard limit: 5 real actions/cycle
VALHALLA_RATE_LIMIT=5                   # Max 5 API requests/second
```

### Lead Processing Rules
1. **No lead shall be processed twice** (deduplication enforced at database level)
2. **No lead score < 40** shall be sent outbound (filter applied before export)
3. **No lead > 2 weeks old** shall be processed (freshness enforced)
4. **No direct contact** to leads before compliance review (all outbound batched, not immediate)
5. **All leads logged** to compliance audit trail (immutable)

### Outbound Request Rules
1. **Max 5 concurrent requests** (no connection pooling explosion)
2. **30-second timeout** per request (kill slow requests)
3. **Exponential backoff** on retry (1s, 2s, 4s, 8s, stop)
4. **Max 3 retries** per failed lead (then quarantine, notify ops)
5. **All requests HTTPS/TLS1.2+** (no plaintext)

### System Safeguards
1. **Process memory limit**: 512MB (OOM killer enforces)
2. **Heartbeat check**: Confirm every 30 seconds (auto-rollback if missed)
3. **Error rate threshold**: > 10% failures → auto-rollback to Phase 3
4. **Outbound health check**: Must succeed at least 1x before batch (no blind export)
5. **Daily restart**: System restarts at 2 AM UTC (clean state)

---

## 3. ALLOWED ACTIONS (Phase 4)

These are the **only operations permitted** once Phase 4 is active.

### Permitted Outbound Actions
- ✅ Export scored leads to partner API
- ✅ Log lead metrics to dashboard (read-only)
- ✅ Send alerts to ops Slack channel
- ✅ Record lead processing telemetry
- ✅ Update lead status in internal database

### Permitted Admin Actions
- ✅ View real-time lead flow dashboard
- ✅ Manually trigger rollback to Phase 3
- ✅ Pause outbound (not stop—preserves queue)
- ✅ Adjust rate limits (with CFO approval)
- ✅ Archive completed lead batches

### **Forbidden Actions** ❌
- ❌ Modify lead scores post-export
- ❌ Change VALHALLA_PHASE env var (requires process restart)
- ❌ Bypass deduplication logic
- ❌ Export leads with score < 40
- ❌ Disable monitoring/alerts
- ❌ Direct contact to leads (must use outbound API batch)
- ❌ Run in production without all 9 gates signed

---

## 4. HARD CAPS (Phase 4 Operational Limits)

| Metric | Limit | Reason |
|--------|-------|--------|
| **Leads per cycle** | 25 (max 100) | Prevent bulk export errors |
| **Actions per cycle** | 5 (max 10) | Control outbound rate |
| **Daily leads** | 10,000 | Budget control |
| **Max lead age** | 14 days | Relevance window |
| **Min lead score** | 40 | Quality threshold |
| **API timeout** | 30s | Prevent hanging requests |
| **Max retries** | 3 | Reduce system stress |
| **Error rate tolerance** | 10% | Auto-rollback trigger |
| **Memory per process** | 512MB | OOM prevention |
| **Max concurrent requests** | 5 | Connection control |

---

## 5. PHASE 4 TRANSITION PROCEDURE

### Step 1: Final Pre-Flight (Day 1, Morning)
```bash
# Verify all 9 gates are signed
python verify_phase4_gates.py

# Confirm 72-hour Phase 3 stability
python verify_phase3_stability.py
```

### Step 2: Update Environment (Day 1, 2 PM UTC)
```bash
# Backup current config
cp .env.sandbox .env.sandbox.phase3-backup

# Update to Phase 4 (manually)
sed -i 's/VALHALLA_PHASE=3/VALHALLA_PHASE=4/g' .env
sed -i 's/VALHALLA_DRY_RUN=1/VALHALLA_DRY_RUN=0/g' .env
sed -i 's/VALHALLA_DISABLE_OUTBOUND=1/VALHALLA_DISABLE_OUTBOUND=0/g' .env
```

### Step 3: Health Check (Day 1, 2:05 PM UTC)
```bash
# Run in Phase 4 with 1 lead only
VALHALLA_MAX_LEADS_PER_CYCLE=1 python SANDBOX_ACTIVATION.py
# Wait 2 minutes, verify export succeeded to real API
```

### Step 4: Scale Gradually (Day 1-3)
- **Hour 1-2**: 1 lead/cycle (manual verification each cycle)
- **Hour 2-6**: 5 leads/cycle (monitor dashboard)
- **Hour 6-24**: 10 leads/cycle (check error rates)
- **Day 2**: 25 leads/cycle (full rate, monitor for 24h)
- **Day 3+**: Normal operations with continuous monitoring

### Step 5: Rollback Condition (Any Time)
```bash
# If error rate > 10% or alert > 5 failures/hour
# STOP immediately and restore
cp .env.sandbox.phase3-backup .env
python SANDBOX_ACTIVATION.py  # Returns to Phase 3 DRY-RUN
```

---

## 6. STAKEHOLDER SIGN-OFFS

### [ ] CEO / Executive Leadership
- **Name**: ___________________________
- **Date**: ___________________________
- **Signature**: ___________________________
- **Comments**: ___________________________

### [ ] CFO / Finance
- **Name**: ___________________________
- **Date**: ___________________________
- **Signature**: ___________________________
- **Comments**: ___________________________

### [ ] General Counsel / Legal
- **Name**: ___________________________
- **Date**: ___________________________
- **Signature**: ___________________________
- **Comments**: ___________________________

### [ ] Chief Risk Officer
- **Name**: ___________________________
- **Date**: ___________________________
- **Signature**: ___________________________
- **Comments**: ___________________________

### [ ] Head of Operations
- **Name**: ___________________________
- **Date**: ___________________________
- **Signature**: ___________________________
- **Comments**: ___________________________

---

## 7. CONTACT & ESCALATION

**Phase 4 Operations Lead**: [ops-lead@company.com](mailto:ops-lead@company.com)  
**On-Call Escalation**: [ops-oncall@company.com](mailto:ops-oncall@company.com)  
**Emergency Rollback**: Press red button at [dashboard-url] or call ops hotline  

**Phase 4 Slack Channel**: #valhalla-phase4-live  
**Status Page**: [ops-dashboard.company.com](http://ops-dashboard.company.com/)  
**Runbook**: [confluence/phase4-runbook](http://confluence/phase4-runbook)

---

## 8. REVISION HISTORY

| Date | Version | Author | Change |
|------|---------|--------|--------|
| 2026-01-08 | 1.0 | Valhalla Admin | Initial Phase 4 policy definition |

---

## APPROVAL

**This document is DRAFT pending stakeholder sign-offs.**

Once all 5 stakeholders have signed Section 6, Phase 4 may be activated with explicit approval from CEO.

**Expected Approval Date**: 2026-01-15 (pending reviews)

---

## Phase 4 Authorization & Sign-Off

By signing below, stakeholders confirm:
- Phase 3 passed stability + safety certification
- Guard enforcement is active
- DRY-RUN and outbound constraints are understood
- Phase 4 will proceed in pilot mode only
- Rollback procedures are defined and tested

### Signatures

CEO: _______________________  Date: __________  
CFO: _______________________  Date: __________  
Risk Officer: _______________  Date: __________  
Legal Liaison: ______________  Date: __________  
Operations: _________________  Date: __________  

Version: Phase 4 Policy v1.0  
Authorized On: __________  

---

*End of Phase 4 Policy Document*
