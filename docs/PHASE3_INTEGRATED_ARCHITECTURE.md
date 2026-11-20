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
9. AUTHORITY_CHECK (existing delegated mandate; OWNER_APPROVAL when required)
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


## Owner-confirmed system-wide Pantheon doctrine — 2026-11-20

This clarification governs the interpretation of earlier single-opportunity and owner-approval diagrams. The AI Gods are persistent, cross-system specialist intelligences, NOT merely a committee invoked for one opportunity. Every God covers every authorized Valhalla subsystem relevant to that God's specialty, across Prime's five initial legacies, future clones, Product/Venture Foundries, research, development, operations, investments, finance, trusts, insurance, residency, protection and other mapped capabilities. Coverage means scoped, least-privilege access and meaningful analysis; it does not grant unrestricted database access or external action permission.

Specialists receive relevant events and scheduled work, independently monitor and research their domains, proactively identify risks/opportunities, report evidence, recommendations, uncertainties and urgency to Heimdall Prime through the controlled bridge, and revisit affected decisions when new material evidence arrives. Loki is the independent cross-system adversarial specialist: he challenges both Heimdall proposals and relevant specialist findings, preserves contrary evidence and dissent, and re-reviews material revisions. Heimdall must take Loki's material findings into account rather than silently discard them.

Heimdall Prime is the sole central operational decision-maker and coordinator. He synthesizes relevant specialist reports and Loki's independent challenge, selects or revises an action, checks deterministic authority/risk/capital/legal constraints, and dispatches and verifies the best permitted action. Routine authorized actions do NOT require a new owner prompt or per-action owner approval. Owner A/B/C/Override briefings are reserved for decisions outside delegated mandates, unresolved material exceptions, or actions requiring specific owner or qualified professional authorization. This doctrine does not expand live permissions, change deployment rules, remove hard safety/legal stops or permit unapproved spending. Gods cannot grant themselves authority; independent review is proportionate to risk, with required missing/stale review holding the affected action.

Acceptance: maintain a responsibility-to-subsystem coverage map with authorized inputs and report schemas; demonstrate proactive event-driven AND scheduled analysis (not only a manually called API); preserve independent version-bound Loki dissent and Heimdall's recorded response; show cross-business specialist reporting, owner-private access boundaries, delegated routine execution without repeated owner prompts, escalation outside mandates, and reconciled outcomes feeding Mimir. Test failures, stale evidence, missing specialist review, tenant isolation, rate/cost controls and restart recovery. Exact historical names and overlapping specialty assignments still require source reconciliation; do not invent new agents or treat a role list as proof of deployment.

Status: owner-confirmed architecture requirement only; no new worker, schedule, provider integration, or production deployment is certified by this clarification.
