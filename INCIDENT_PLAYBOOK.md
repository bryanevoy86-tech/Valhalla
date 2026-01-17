# INCIDENT PLAYBOOK — WHEN SOMETHING BREAKS

Goal: recover fast without breaking the canon.

---

## Severity levels
- INFO: no impact
- WARNING: partial impact, workaround exists
- CRITICAL: system unsafe or blocking revenue flow

---

## 1) If an outbound action occurs in SANDBOX (CRITICAL)

1) Immediately set engine state to DORMANT (step-down requires transitions; if you can't step down, set operationally: STOP outbound use)

2) Disable worker/dispatcher processes if any

3) Identify the path:
   - Was it a router endpoint missing enforce_engine?
   - Was it a worker dispatch that bypassed routers?

4) Patch:
   - Add guard_outreach() or guard_contract_send() at dispatch point

5) Add an incident outcome record

---

## 2) If API returns 500 in runbook path (CRITICAL)

Runbook must never 500.

1) Check `/api/runbook/status` implementation

2) Wrap logic with try/except and return blockers

3) Confirm fixed: runbook responds under failure conditions

---

## 3) If system is BLOCKED and you don't know why (WARNING/CRITICAL)

1) Open `/api/runbook/status`

2) Read blockers list

3) Resolve blockers:
   - missing env vars
   - missing policies
   - metrics invalid
   - quarantine backlog too high

4) Re-check runbook

---

## 4) If data poisoning suspected (CRITICAL)

1) Stop promotions to CLEAN

2) Keep intake quarantined

3) Review sources and evidence refs

4) Downgrade trust tiers as needed

5) Resume promotions only after verification discipline is restored

---

## 5) If outcomes are not being recorded (WARNING)

Outcomes are how the system learns.

1) Reduce scope (fewer leads worked per day)

2) Make outcome recording mandatory at end of each interaction

3) Resume scale only when outcomes ratio improves

---

## 6) Recovery principle (locked)

If uncertain, remain in SANDBOX.

**Survival > speed.**
