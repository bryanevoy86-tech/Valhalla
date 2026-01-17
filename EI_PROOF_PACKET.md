# EI PROOF PACKET — VALHALLA / HEIMDALL (CANADA)

Purpose: Provide EI with clear evidence that you have:
- a real business plan,
- a real operating system,
- risk controls,
- measurable milestones,
- and governance that prevents reckless behavior.

This document is designed to be printed or used as a screen-share checklist.

---

## 1) Business Summary (1 minute)
- Business: Canada-wide real estate wholesaling operations (initial engine)
- System: Valhalla/Heimdall operating platform
- Method: Intake -> Verify -> Score -> Decide -> Execute (human sign-off)
- Controls: Runbook + gates + sandbox/active states (fail-safe)

---

## 2) Show these screens (Screenshots requested by EI)

### 2.1 Runbook Status (authority screen)
- Open: `/api/runbook/status`
- Show:
  - `ok` flag
  - blockers list
  - warnings list
  - metrics snapshot
  - engine states

Screenshot name: `EI_01_Runbook_Status.png`

### 2.2 Engine Control (safety enforcement)
- Open: `/api/engines/states`
- Show:
  - wholesaling is SANDBOX during early phase
  - other engines DORMANT

Screenshot name: `EI_02_Engine_States.png`

### 2.3 Quarantine Intake (data purity)
- Open: `/api/intake/quarantine`
- Show:
  - items are quarantined by default
  - promotion exists and is controlled

Screenshot name: `EI_03_Quarantine.png`

### 2.4 Outcomes (closed-loop learning)
- Open: `/api/outcomes`
- Show:
  - append-only evidence tracking
  - reason + notes + timestamp

Screenshot name: `EI_04_Outcomes.png`

### 2.5 Metrics (financial truth + burn control)
- Open: `/api/metrics`
- Show:
  - monthly burn
  - outcomes requirements
  - clean promotion enabled

Screenshot name: `EI_05_Metrics.png`

---

## 3) Explain the safety model (simple language)
- The system can run in SANDBOX using real data.
- In SANDBOX, it cannot send emails/texts/contracts or trigger outbound actions.
- Only after safety checks pass can the system be moved to ACTIVE.
- Even in ACTIVE, the runbook can block risky operation.

---

## 4) Milestones (what EI wants: "how do you know it's working?")

### Milestone 1: System supports itself
- Target: monthly net >= monthly burn
- Evidence: runbook + metrics + closed-loop outcomes

### Milestone 2: Consistent deal flow
- Evidence: intake volume, qualification rate, offer rate, close rate

### Milestone 3: Canada-wide scale
- Evidence: stable workflow, controlled quarantine backlog, stable outcomes

---

## 5) Weekly accountability plan (EI-friendly)
- Weekly review of:
  - runbook blockers
  - outcome ratios
  - quarantine backlog
  - financial burn vs net
- Adjust scope only if stable

---

## 6) If EI asks "what stops you from reckless scaling?"
Answer:
- Engine guards + runbook authority
- SANDBOX blocks outbound actions
- ACTIVE requires explicit promotion and passing checks
- Closed-loop outcomes force learning and correction
- Data purity prevents bad inputs poisoning the system

---

## 7) "What are you doing daily?"
- Check runbook
- Process intake + promote clean
- Work leads
- Record outcomes
- Review alerts

---

## 8) Attachments to include (optional)
- GO_LIVE_CHECKLIST.md
- OPS_RUNBOOK.md
- INCIDENT_PLAYBOOK.md
