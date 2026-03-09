# ENGINE REGISTRY

Complete inventory of all engines, candidates, and side hustles.

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Certified |
| ⏳ | In Progress |
| 🔵 | Candidate |
| 🔴 | Blocked |
| 📦 | Archived |

## Active Engines

| Engine | Status | Solo | Integrated | Ready | Notes |
|--------|--------|------|------------|-------|-------|
| Valhalla Core | ✅ ACTIVE | ✅ | ✅ | ✅ | Primary system, Phase 3 certified |

**Valhalla Core Status:**
- Current phase: Phase 3 (Dry-Run, Real Data)
- 72-hour certification: IN PROGRESS
- Expected completion: 2026-01-11 05:52 UTC
- Guard enforcement: DRY_RUN=1, OUTBOUND_DISABLED=1 (locked)

## Candidate Engines

| Engine | Category | Status | Intake | Solo | Integrated | Notes |
|--------|----------|--------|--------|------|------------|-------|
| Storage Cleanouts | Side Hustle | 🔵 CANDIDATE | ⏳ | ⏳ | ⏳ | Fast-track sandbox testing |
| Landscaping | Side Hustle | 🔵 CANDIDATE | ⏳ | ⏳ | ⏳ | Seasonal, reversible |
| Arbitrage | High-Kill | 🔵 CANDIDATE | ⏳ | ⏳ | ⏳ | High signal/noise, needs filtering |

## Engine Lifecycle

```
CANDIDATE
    ↓
    [INTAKE FORM]
    ↓
STAGE 1: SOLO SANDBOX
    [6-hour certification]
    ↓ PASS
STAGE 2: INTEGRATED SANDBOX
    [6-hour certification]
    ↓ PASS
STAGE 3: READY CERT
    [approval gate]
    ↓ APPROVED
PRODUCTION (Phase 4+)
    [live operation]
    ↓
    [periodic review]
    ↓ FAIL → ARCHIVE
```

## Engine Templates

All new engines must complete:

1. **ENGINE_INTAKE.md** — Initial idea capture (STAGE 0)
2. **ENGINE_SOLO_SANDBOX_CERT.md** — Standalone testing (STAGE 1)
3. **ENGINE_INTEGRATED_SANDBOX_CERT.md** — Coexistence testing (STAGE 2)
4. **ENGINE_READY_CERT.md** — Pre-production approval (STAGE 3)

See `/engines/templates/` directory.

## Side Hustle Fast Track

Side hustles follow a faster path via **SIDE_HUSTLE_FAST_SANDBOX.md**:

```
CANDIDATE → FAST SANDBOX (1-3 hours) → PROMOTE/PARK/ARCHIVE
```

Criteria: Quick signal detection, not perfection.

## Blocked Engines

None currently. (Blocked status used for rejected ideas that may be revisited.)

## Archived Engines

None currently. (Archive used for engines that failed certification or were deliberately shelved.)

## Registry Update Frequency

- Real-time: New candidates added immediately to INTAKE
- Daily: Status updates during testing phases
- Weekly: Formal review of STAGE 1+ candidates
- Monthly: Strategic review of portfolio

---

*Last updated: 2026-01-09*  
*Maintained by: Governance System*
