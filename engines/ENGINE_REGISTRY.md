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

## Owner doctrine and canonical economic intake — November 21, 2026

Valhalla continuously compares ways to meet the owner's objectives. The platform, protected reserves, reusable assets and verified lessons outlast any venture. Historical ideas, ongoing operations, and newly discovered opportunities compete on the same forward-looking economics. The lifecycle above records historical readiness requirements. No candidate category is mandatory at startup, and a registry row confers no activation authority.

| Recovered family | Existing anchors | Treatment |
|---|---|---|
| Local services | Storage cleanouts and landscaping above | Historical candidates |
| Real estate | Wholesale, BRRRR, flips, rentals, multifamily and commercial in the canonical planned catalog and Million-Path strategy | Optional playbooks |
| Acquisitions and digital businesses | Business acquisitions, AI/passive microbusinesses, SaaS, AI automation services, micro-SaaS and lead generation | Candidate or existing business with dated operating evidence |
| Information and operations | Market intelligence, data products, funding/grants, and operations automation | Optional capabilities or revenue candidates depending on economics |
| Capital strategies | Historical inventory arbitrage, Package 7 paper FX and trading advisory | Advisor-only or simulation. The older percentage allocation design does not assign protected capital. |

The current planned catalog is `PLANNED_ENGINE_CATALOG` in the canonical Completion Registry. `GET /api/prime/economy/historical-candidates` recovers those candidates with their recorded registry states when present. `POST /api/prime/economy/opportunities` adds versioned, scope-bound comparison records for discoveries, operating businesses, Foundry items and historical playbooks. Suspended and rejected rows stay traceable and are excluded from eligible rankings. Specify source, activation requirements, dependencies, human involvement and downside. Record actual operator performance separately. No historical catalog setting grants trade, commercial, or financial authority.

### Scoped startup intake

Authorized local demand and procurement exports enter `POST /api/prime/foundry/intake`. Each job binds a registered source and observation key, dated freshness, citation, buyer segment, sample and demand counts, and an exact Legacy scope. The worker creates digest-checked Foundry evidence and wakes existing specialist assignments. Revenue models can be described for previously unknown opportunity categories. The Universal Evaluator provides a shadow recommendation and the economic registry compares its source-bound demand and economics within the mandate and currency. Candidate intake has no activation authority.
