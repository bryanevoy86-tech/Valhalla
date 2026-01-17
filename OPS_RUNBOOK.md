# OPS RUNBOOK — DAILY OPERATIONS (WHOLESALING ENGINE)

This is your daily operating manual.

---

## 1) Start of day (10 minutes)

1) Open runbook:
```
GET /api/runbook/status
```

2) If blockers exist:
- Stay SANDBOX
- Resolve blockers before doing any system-triggered outbound

3) Check engine state:
```
GET /api/engines/states
```

---

## 2) Intake (daily)

1) Add leads to quarantine:
```
POST /api/intake
{
  "item_id": "lead_123",
  "source": "kijiji",
  "entity_type": "lead",
  "payload": {...}
}
```

2) Review quarantine:
```
GET /api/intake/quarantine
```

3) Promote CLEAN only when verified:
```
POST /api/intake/admin/promote
{
  "item_id": "lead_123",
  "trust_tier": "T2"
}
```

---

## 3) Work pipeline

- Score / match / summarize inside the system (allowed in SANDBOX)
- Do manual outreach outside the system if still in SANDBOX
- Once ACTIVE (runbook ok), you may use system outreach endpoints

---

## 4) Evidence logging (non-negotiable)

Every day, record outcomes:
```
POST /api/outcomes
{
  "entity_type": "lead",
  "entity_id": "lead_123",
  "outcome": "won",
  "reason": "price",
  "notes": "Seller agreed at $X",
  "evidence_ref": "ref_456"
}
```

Minimum outcomes to record:
- contact attempt result
- qualification result
- offer sent response
- deal accepted/rejected
- buyer response

---

## 5) Metrics updates (weekly or when burn changes)

```
POST /api/metrics
{
  "monthly_burn_cad": 15000,
  "monthly_net_cad": 5000,
  "outcomes_required_ratio": 1.0,
  "critical_runbook_blockers": 0
}
```

Update:
- monthly_burn_cad
- monthly_net_cad
- outcomes requirements
- clean promotion flag

---

## 6) End of day (5 minutes)

- Record outcomes for anything touched today
- Check runbook once more
- Note any incidents or near misses

---

## 7) Expansion rule

Do not expand scope unless:
- runbook remains clean
- outcomes recording is consistent
- quarantine backlog remains controlled
- you personally feel workload is manageable
