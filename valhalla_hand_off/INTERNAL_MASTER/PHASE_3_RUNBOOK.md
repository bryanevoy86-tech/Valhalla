# Phase 3 Runbook (INTERNAL — DO NOT SHARE)

## Goal
Inject real lead data into Valhalla while keeping all irreversible actions locked.
- Real data IN
- DRY-RUN ON  
- Outbound DISABLED

## Safety invariants (must always be true)
- `VALHALLA_DRY_RUN=1`
- `VALHALLA_DISABLE_OUTBOUND=1`
- `VALHALLA_PHASE=3`
- `VALHALLA_REAL_DATA_INGEST=1`

If any of these are violated, the system must hard-stop before executing.

## Startup

1) Load sandbox environment config:
```bash
source .env.sandbox
```

2) Start sandbox runner:
```bash
python SANDBOX_ACTIVATION.py
```

3) Guard will validate constraints at startup. If any violation detected, process exits with:
```
PHASE 3 SAFETY VIOLATION: VALHALLA_DRY_RUN must be enabled...
PHASE 3 SAFETY VIOLATION: Outbound must be disabled...
```

## Inputs

Drop lead files into:
```
data/inbox/real_leads/
```

Supported formats:
- CSV: `lead_id, first_name, last_name, phone, email, address, city, province, postal_code, source, notes, asking_price, bed, bath, sqft`
- JSON: Array of objects with flexible schema (will be parsed)

If data is malformed or suspicious, manually move to:
```
data/inbox/quarantine/
```

## Outputs

Real lead exports are written to:
```
ops/exports/sandbox_leads_TIMESTAMP.csv
```

Format:
```
lead_id,score,source
LEAD_001,65,Website
LEAD_002,80,Referral
```

Scores range 0-100. Distribution should be normal (not pinned to 0 or 100).

## What to watch

- **Ingestion success messages** — Check logs for lead parse/import status
- **Dedupe behavior** — No repeated lead IDs in exports
- **Scoring distribution** — Verify NOT all 0 or all 100 (indicates system collapse)
- **No outbound attempts** — Must remain disabled (DRY-RUN enforced)
- **DRY-RUN confirmations** — Any action-like steps should log "DRY-RUN" or "not executed"

## Guard verification (repeat any time you change env/config)

**Test 1: Verify DRY-RUN must be ON**
```bash
export VALHALLA_DRY_RUN=0
python SANDBOX_ACTIVATION.py
```
Expected: Hard-fail with `PHASE 3 SAFETY VIOLATION: VALHALLA_DRY_RUN must be enabled`

**Test 2: Verify outbound must be OFF**
```bash
export VALHALLA_DRY_RUN=1
export VALHALLA_DISABLE_OUTBOUND=0
python SANDBOX_ACTIVATION.py
```
Expected: Hard-fail with `PHASE 3 SAFETY VIOLATION: Outbound must be disabled`

Then restore .env.sandbox settings.

## Exit criteria for Phase 3

Phase 3 can move to Phase 4 (human approval + real transactions) when:

- Stable ingestion over time (no crashes, multiple cycles)
- Clean dedupe and routing (no ID collisions)
- No unsafe actions possible (guards proven, DRY-RUN locked)
- Logs show consistent loop health (no escalating errors)

## DO NOT DO

- Do **NOT** enable outbound during Phase 3
- Do **NOT** change safety caps impulsively  
- Do **NOT** activate multiple legacies at once
- Do **NOT** proceed to Phase 4 without human review

## Transition to Phase 4

When Phase 3 is stable and passing, prepare for Phase 4:
1. Human review of Phase 3 logs and exports
2. Decision: GO → Phase 4 (real transactions) or NO-GO → repeat Phase 3
3. If GO: Update env vars (DRY-RUN=0, VALHALLA_PHASE=4)
4. If NO-GO: Investigate issue, do NOT force

Phase 3 is the last safety checkpoint before irreversible actions.
