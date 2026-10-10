# Winnipeg Test Fixture Certification

Generated: 2026-10-10
Scope: Clean-state reproducibility for Winnipeg Phase Two certification tests

## Failure Cause (Pre-Fix)
- Clean candidate run failed at `phase2_winnipeg_certification_route_returns_rankings_and_shadow_safety` with HTTP 409 (`insufficient Winnipeg anchors`).
- Canonical CSV sources supplied only 3 Winnipeg anchors with positive asking price.
- Route threshold requires at least 10 anchors.
- Passing development runs depended on fallback records from local `valhalla_local.db`.

## Root Cause Proof
- CSV anchor counts:
  - `data/inbox/real_leads/sample_leads_01.csv`: Winnipeg positive anchors = 3
  - `data/inbox/real_leads/batch_01_leads.csv`: Winnipeg positive anchors = 0
  - `data/inbox/real_leads/batch_02_leads.csv`: Winnipeg positive anchors = 0
  - `data/inbox/real_leads/batch_03_leads.csv`: Winnipeg positive anchors = 0
- Fallback local DB evidence (passing developer state):
  - table: `deals`
  - Winnipeg-like rows: 365
  - fallback query fields used by route: `id`, `title`, `arv`, `estimated_repair_cost`

## Dependency Classification
- `deals` fallback records from local `valhalla_local.db`: `PRODUCTION_DATA_ACCIDENTALLY_DEPENDED_ON`
- CSV anchors under `data/inbox/real_leads/*`: `TEST_FIXTURE_REQUIRED`
- Any dependency on developer-local DB state for this test path: `UNNECESSARY_DEPENDENCY`

## Deterministic Fixture Design
- Implemented in test-only code at `services/api/tests/test_completion_registry.py`.
- Added helper `_seed_winnipeg_anchor_fixture(...)` to create deterministic Winnipeg CSV anchors in a per-test temporary working directory.
- Seeded records: 12 rows in `data/inbox/real_leads/sample_leads_01.csv`.
- Data properties:
  - non-sensitive synthetic addresses/prices
  - deterministic values
  - offline and small footprint

## Fixture Usage Assertions
- Initial fixture file absent assertion before seed.
- Seed step assertion confirms 12 rows written.
- Local `valhalla_local.db` absence asserted in temp working directory.
- Response assertions confirm evaluation sources are CSV paths and do not reference `valhalla_local.db`.

## Production Rule Preservation
- No production threshold changes were made.
- No minimum-anchor, confidence, source, or decision-quality safeguards were lowered.
- Route/runtime behavior remains unchanged; only test setup was made deterministic.

## Test Fixture vs Real Data
- `TEST_FIXTURE_CERTIFICATION` proves deterministic pipeline/path behavior in test harness conditions.
- `REAL_DATA_CERTIFICATION` proves behavior against current live/canonical Winnipeg source data.
- These certifications are not equivalent.

## Reproducibility Results
- Fresh DB targeted run #1 (Winnipeg test): PASS
- Fresh DB targeted run #2 (Winnipeg test): PASS
- Fresh DB focused suite (`services/api/tests/test_completion_registry.py`): 58 passed, 0 failed, 0 errors, 0 skipped
- Clean-checkout run #1 (no local `valhalla_local.db`, fresh DB path): 58 passed, 0 failed, 0 errors, 0 skipped
- Clean-checkout run #2 (no local `valhalla_local.db`, different fresh DB path): 58 passed, 0 failed, 0 errors, 0 skipped

## Phase Two / Phase Three Regression
- Phase Two regression slice (property identity/source/micro-market/underwriting/pantheon/role safety/Winnipeg/shadow): PASS
- Bad-deal/exit/replay/holdout/challenger slice: PASS
- Full focused Phase Three suite: PASS (58/0/0/0)

## Broad Parity
- Feature branch collect-only errors: 0
- Baseline origin/main collect-only errors: 0
- Introduced regressions: 0
