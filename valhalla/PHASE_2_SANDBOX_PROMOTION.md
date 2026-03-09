# VALHALLA PHASE 2 — Move Engines to SANDBOX

**Status**: Ready to execute
**Current**: Engines DORMANT, go_live.enabled = true
**Goal**: Engines in SANDBOX (logic runs, no real-world impact)

---

## ✅ What PHASE 2 Does

Promotes engines from **DORMANT → SANDBOX**:

- ✅ Logic runs
- ✅ Data flows
- ✅ Audits/logs populate
- ❌ No money moves
- ❌ No real outreach
- ❌ No irreversible actions

---

## 🚀 PHASE 2 Execution

### STEP 1: Promote Wholesaling to SANDBOX

```bash
python valhalla/promote_engine.py --engine wholesaling --state sandbox
```

**Expected output:**
```
✓ Engine promoted
New state:
  state: SANDBOX
  allowed_next: [LIVE]
  ...
```

**What happens:**
- Wholesaling engine enters SANDBOX
- Can process leads, score deals, generate offers
- NO live offers sent
- NO real follow-ups queued

---

### STEP 2: Promote Trading Advisory to SANDBOX

```bash
python valhalla/promote_engine.py --engine trading_advisory --state sandbox
```

**Expected output:**
```
✓ Engine promoted
New state:
  state: SANDBOX
  allowed_next: [LIVE]
  ...
```

**What happens:**
- Trading advisory engine enters SANDBOX
- Can generate signals, record advisories
- "Advisory only" boundary enforced
- NO trades placed

---

### STEP 3: Verify Engine States

```bash
curl -s https://valhalla-api-ha6a.onrender.com/api/engines/states | python -m json.tool
```

**Expected:**
```json
{
  "engines": [
    {
      "engine_name": "wholesaling",
      "state": "SANDBOX",
      "allowed_next": ["LIVE"],
      "changed_by": "heimdall-phase-2",
      "reason": "PHASE 2: Promote wholesaling from DORMANT to SANDBOX"
    },
    {
      "engine_name": "trading_advisory",
      "state": "SANDBOX",
      "allowed_next": ["LIVE"],
      "changed_by": "heimdall-phase-2",
      "reason": "PHASE 2: Promote trading_advisory from DORMANT to SANDBOX"
    }
  ]
}
```

---

## 🔍 PHASE 2 Validation (Do Not Skip)

### Wholesaling Engine in SANDBOX

Confirm it:
- [ ] Accepts test leads (no real incoming data yet)
- [ ] Scores deals using actual logic
- [ ] Generates offers/scripts (database writes, not sent)
- [ ] Queues follow-ups (in queue table, not executed)
- [ ] Writes logs to audit trail
- [ ] Does NOT send live offers to contacts
- [ ] Does NOT make API calls to external services

**Test command** (after deployment):
```bash
curl -X POST https://valhalla-api-ha6a.onrender.com/api/intake/leads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Lead SANDBOX",
    "email": "sandbox@test.local",
    "phone": "555-0000",
    "property_address": "123 Test St"
  }'
```

Check:
- Log created in database
- No external API calls in runbook
- Offer queued but not sent

---

### Trading Advisory Engine in SANDBOX

Confirm it:
- [ ] Generates signals from market data
- [ ] Records advisories in database
- [ ] Respects "advisory only" boundary
- [ ] Does NOT place trades
- [ ] Writes to audit log
- [ ] All behavior is read-only externally

---

## 📋 PHASE 2 Checklist

- [ ] Go-live still enabled (go_live_enabled = true)
- [ ] Kill-switch disengaged (kill_switch_engaged = false)
- [ ] Wholesaling engine state = SANDBOX
- [ ] Trading advisory engine state = SANDBOX
- [ ] Both allowed_next = ["LIVE"]
- [ ] Wholesaling generates test offers without sending
- [ ] Trading advisory generates test signals without trading
- [ ] Runbook status shows no blockers
- [ ] All engines logging correctly

---

## 🎯 Next: PHASE 3 (After Validation)

Once SANDBOX validation passes:

```bash
# Promote ONE engine to LIVE (start with wholesaling)
python valhalla/promote_engine.py --engine wholesaling --state live

# Then trading_advisory
python valhalla/promote_engine.py --engine trading_advisory --state live
```

At that point, Heimdall takes over as system observer and policy enforcer.

---

**Ready? Execute the commands in STEP 1-3, then report back with validation results.**
