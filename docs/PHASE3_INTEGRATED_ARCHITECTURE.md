# Phase 3 Integrated Architecture

Status: BUILT - NEEDS TESTING (full-stack), PROVEN (focused completion registry suite)

## Objective
Integrate the universal opportunity pipeline into one canonical flow with historical replay safeguards, immutable prediction snapshots, universal outcome contracts, capital/risk/exit gating, and champion/challenger controls.

## Canonical Flow
1. DISCOVERY
2. UNIVERSAL_OPPORTUNITY
3. EVIDENCE
4. SPECIALIST_ANALYSIS
5. PANTHEON_WAR_TABLE
6. CAPITAL_RISK_EXIT_ANALYSIS
7. HEIMDALL_INITIAL_RECOMMENDATION
8. HEIMDALL_FINAL_RECOMMENDATION
9. OWNER_APPROVAL
10. BOUNDED_EXECUTION
11. ACTUAL_OUTCOME
12. MIMIR_LEARNING

## Integrated Controls
- Immutable prediction snapshots (`prediction_snapshot_id`, `prediction_locked_at`, `immutable=true`).
- Universal outcome contract scaffold attached to each decision.
- Holdout contamination protection: reveal of holdout outcomes blocked when `tuning_mode=true`.
- Challenger model enforcement: challenger execution is shadow-only.
- Replay metadata (`replay_mode`, `replay_partition`) included in outputs.
- Recovery/exit protocol and capital/risk/exit analysis emitted per opportunity.

## Current Implementation Anchors
- Shared evaluator service:
  - `services/api/app/services/universal_opportunity_evaluator.py`
- Canonical endpoint wiring:
  - `services/api/app/routers/completion_registry.py`
- Guardrail and contract tests:
  - `services/api/tests/test_completion_registry.py`

## Status Classification
- Universal evaluator extraction: BUILT - NEEDS TESTING (cross-module)
- Replay/holdout/challenger controls: PROVEN (focused tests)
- Universal outcome contract emission: PROVEN (focused tests)
- Baseline/collection parity against baseline worktree: PROVEN (no introduced collection regressions)
