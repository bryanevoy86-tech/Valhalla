# VALHALLA / HEIMDALL — GO-LIVE CHECKLIST (LOCKED CANON)

This checklist is authoritative. No step is optional unless marked OPTIONAL.

---

## 0) Definitions (Non-negotiable)

### Engine States
- DISABLED: cannot run
- DORMANT: exists but cannot run
- SANDBOX: real-world data allowed, real-world effects blocked
- ACTIVE: real-world effects allowed (still subject to runbook + gates)

### Real-world effects (blocked in SANDBOX)
- SMS / Email / Calls
- Webhooks / External notifications
- Disposition sends / Buyer blasts
- E-signature send requests
- Any money movement / execution

---

## 1) Must-pass items before ACTIVE (Required)

### 1.1 Runbook is operational
- [ ] API is running
- [ ] `/api/runbook/status` responds (never 500)
- [ ] Runbook reports `ok: false` when blockers exist (expected until configured)
- [ ] Runbook reports `ok: true` only when configured and safe

### 1.2 Engine guard enforcement verified
- [ ] Set engine: wholesaling -> SANDBOX
- [ ] Verify 409 EngineBlocked on ALL outbound endpoints:
  - /messaging/send-email
  - /messaging/send-sms
  - /notify/webhook
  - /notify/email
  - /docs/send
  - /legal/sign
  - /admin/heimdall/api/alerts/test (if enabled)
- [ ] Verify inbound webhooks remain allowed (no guards on inbound)

### 1.3 Service-layer dispatch guard (Recommended for real outreach)
- [ ] Dispatch workers (outbox/webhook) enforce guard_outreach() at dispatch point
- [ ] Messaging service enforces guard_outreach() at vendor send point
- [ ] E-sign service enforces guard_contract_send() at vendor send point

### 1.4 Metrics configured (truthful numbers)
- [ ] Set monthly_burn_cad (realistic)
- [ ] Set monthly_net_cad (0 until real)
- [ ] Set outcomes_required_ratio (start at 1.0 or lower only if you accept weaker learning)
- [ ] Set clean_promotion_enabled = true
- [ ] Confirm metrics endpoint returns expected values: `/api/metrics`

### 1.5 Closed-loop outcomes enforced (Gate #2)
- [ ] Outcome recording endpoint works: `/api/outcomes`
- [ ] Minimum daily habit: record outcomes for:
  - contact attempts
  - lead qualification results
  - deal accepted/rejected
  - buyer responses

### 1.6 Data purity enforced (Gate #3)
- [ ] Intake routes default to QUARANTINE
- [ ] Promotion to CLEAN requires explicit action
- [ ] Quarantine backlog visible and controlled
- [ ] Clean promotion remains enabled

---

## 2) Soft Launch Plan (Recommended)

### Phase A — SANDBOX soft launch (7–14 days)
- [ ] Run production with wholesaling = SANDBOX
- [ ] Allow real intake, scoring, matching, dashboards
- [ ] Do NOT send messages/contracts from system (manual ok outside system)
- [ ] Collect outcomes daily
- [ ] Stabilize data purity workflow

### Phase B — ACTIVE limited scope (1 market / low volume)
- [ ] Move wholesaling SANDBOX -> ACTIVE ONLY if runbook ok: true
- [ ] Limit outbound volume (manual cap)
- [ ] Continue outcome logging
- [ ] Review runbook daily

### Phase C — Canada-wide scale
- [ ] Expand only after stable weeks with low incidents
- [ ] Keep quarantine backlog under control
- [ ] Maintain outcome ratio targets

---

## 3) Go/No-Go Decision (Hard Rule)
GO-LIVE to ACTIVE is allowed only if:
- [ ] Runbook ok: true
- [ ] No critical blockers
- [ ] Engine state transitions are step-by-step (no skipping)
- [ ] Guard enforcement tests pass

If any fail -> remain in SANDBOX.

---

## 4) Daily Operator Checklist (Minimum)
- [ ] Check `/api/runbook/status`
- [ ] Review quarantine backlog + promote CLEAN as needed
- [ ] Review tasks/leads
- [ ] Record outcomes
- [ ] Review alerts (warnings/criticals)
- [ ] Do not expand scope unless stable

---

## 5) Weekly Review Checklist
- [ ] Outcome ratios: recorded vs required
- [ ] Quarantine backlog trend
- [ ] Conversion funnel: intake -> qualified -> offer -> contract -> closed
- [ ] Incident log review
- [ ] Adjust burn/net numbers honestly
- [ ] Keep SANDBOX available for new engines

---

## 6) Dormant Engines Policy (Locked)
- Trading advisory engine remains DORMANT until:
  - wholesaling is self-supporting
  - months of stability
  - separate capital domain confirmed
  - explicit promotion to SANDBOX first (real data only)
