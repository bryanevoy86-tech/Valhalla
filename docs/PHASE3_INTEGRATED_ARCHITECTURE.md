# Phase 3 Integrated Architecture

Status: BUILT - NEEDS TESTING (main-candidate full-stack), PROVEN (focused completion registry suite)

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
- Outcome classes explicitly include `HISTORICAL_OUTCOME`, `SHADOW_OUTCOME`, and `VALHALLA_OUTCOME`.
- Holdout contamination protection: reveal of holdout outcomes blocked when `tuning_mode=true`.
- Replay contamination hard-block: look-ahead leakage returns `409` with `LOOKAHEAD_LEAKAGE_BLOCKED`.
- Challenger model enforcement: challenger execution is shadow-only.
- Replay metadata (`replay_mode`, `replay_partition`) included in outputs.
- Recovery/exit protocol and capital/risk/exit analysis emitted per opportunity, including `LEVEL_0_NORMAL` ladder support and structured `point_of_no_return`.
- Systemic blast radius and survival-capital checks are hard gates for `PROCEED`.
- Mimir context retrieval is injected at decision time and emitted in `mimir_linkage`.

## Current Implementation Anchors
- Shared evaluator service:
  - `services/api/app/services/universal_opportunity_evaluator.py`
- Canonical endpoint wiring:
  - `services/api/app/routers/completion_registry.py`
- Guardrail and contract tests:
  - `services/api/tests/test_completion_registry.py`

## Status Classification
- Universal evaluator extraction and router de-duplication: PROVEN (focused tests + duplicate helper removal evidence)
- Replay/holdout/challenger controls: PROVEN (focused tests)
- Universal outcome contract emission and feedback linkage: PROVEN (focused tests)
- Capital/recovery hard gates (systemic, survival, no-entry-without-exit): PROVEN (focused tests)
- Baseline/collection parity against baseline worktree: PROVEN (no introduced collection regressions)
