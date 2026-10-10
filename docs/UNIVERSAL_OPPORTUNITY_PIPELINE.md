# UNIVERSAL VALHALLA OPPORTUNITY PIPELINE (PHASE THREE)

## Objective

Build and certify a universal cross-engine opportunity pipeline that:

- evaluates opportunities across multiple engines using normalized dimensions
- applies engine-specialist analysis before ranking
- routes every candidate through universal Pantheon governance
- preserves Loki and Norns outputs as structured evidence
- reuses owner approval envelope behavior from certified stack
- supports abstention when no candidate meets deployment threshold
- enforces shadow safety counters with zero external side effects

Constraint honored:

- The certified real-estate Pantheon stack was not redesigned.
- Phase Three extends behavior in the completion registry layer while preserving Phase Two flow.

## Canonical Implementation

- Router: services/api/app/routers/completion_registry.py
- Test suite: services/api/tests/test_completion_registry.py
- Certification artifact: docs/_phase3_universal_opportunity_certification.json

## Endpoints Added

1. GET /api/completion/phase3/universal-opportunity/engine-audit
2. POST /api/completion/phase3/universal-opportunity/evaluate
3. POST /api/completion/phase3/universal-opportunity/certify-shadow

## Universal Evaluation Design

Each opportunity is processed in this sequence:

1. Engine routing key resolution.
2. Specialist analysis with domain-specific criteria.
3. Universal Loki objections and fragility checks.
4. Universal Norns forecast labels (MODEL_ESTIMATE / NOT_YET_CALIBRATED).
5. Normalized dimension scoring across capital, speed, margin, downside, automation, owner-time, scalability, and strategic fit.
6. Weighted rank synthesis for cross-engine comparability.
7. Pantheon governance pass/fail and severity aggregation.
8. Best-option selection or abstention.
9. Owner envelope generation with decision rationale.

## Specialist-Per-Engine Behavior

The pipeline uses specialist analysis templates keyed by engine family so opportunity comparisons remain cross-engine while preserving engine-specific logic.

Examples include:

- real estate: structure around deal mechanics, downside containment, and execution friction
- digital products / SaaS: retention, churn-risk, delivery cost, and technical build burden
- automation services: adoption friction, implementation effort, support load, recurring potential

## Universal Pantheon Governance

The universal flow keeps the existing governance spirit while standardizing output into a shared structure:

- overall_allowed
- worst_severity
- blocked_by
- per-god checks and reasons

This allows one decision grammar to rank and filter opportunities regardless of engine origin.

## Abstention Rule

The pipeline explicitly supports abstention when all candidates fail deployment confidence thresholds or governance/safety constraints.

Certification includes an abstention proof case in the JSON artifact with no selected deployment option.

## Shadow Safety

Shadow certification runs in simulation mode and captures side-effect counters. Expected values are zero for:

- external messages
- contract execution side effects
- irreversible ledger actions
- production mutation channels outside approved persistence boundaries

Result in artifact: external_effects_all_zero = true.

## Regression Evidence

Validated current vs baseline classification:

- completion registry suite (Phase Three branch): 47 passed, 0 failed.
- governance slice in current worktree: 20 failures, all 404 Not Found.
- governance slice in clean baseline worktree from origin/main: same 20 failures, same signature.
- full backend suite in current worktree: interrupted by 5 collection errors.
- full backend suite in clean baseline worktree: same 5 collection errors.

Classification:

- Introduced regressions from Phase Three changes: 0
- Governance 404 slice: PRE-EXISTING / ROUTE-MOUNT OR TEST-HARNESS MISMATCH
- Full-suite collection errors: PRE-EXISTING / IMPORT-CONTRACT AND SCHEMA-COLLECTION DEFECTS

## Certification Scope and Limits

Proven in this phase:

- universal ranking/evaluation path is implemented and exercised
- cross-engine audit and shadow certification endpoints are functional
- abstention behavior is available and evidenced
- no new regressions were introduced relative to baseline failure profile

Not proven in this phase:

- production external integrations or live finance effects (out of scope)
- pre-existing governance mount defects outside completion registry scope

## Required Artifacts

- docs/_phase3_universal_opportunity_certification.json
- docs/UNIVERSAL_OPPORTUNITY_PIPELINE.md (this file)

## Status Classification

- Phase Three universal opportunity pipeline: BUILT - NEEDS TESTING (full-repo harness remains pre-existing unstable)
- Completion registry Phase Three surface: PROVEN in local router-focused regression context
- System-wide governance slice outside this surface: PRE-EXISTING DEFECT (not introduced here)
