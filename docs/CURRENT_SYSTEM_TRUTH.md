# CURRENT SYSTEM TRUTH

Generated: 2026-10-10

## Canonical Backend
- Canonical app entrypoint: `app.main:app` (wrapper) -> `services/api/app/main.py`.
- Router loading strategy: autoload from `app.routers` and `app.routes` packages.

## WeWeb Auth Router
- Source file: `services/api/app/routers/auth_weweb.py`.
- Prefix: `/api/weweb`.
- Local source endpoints:
  - `POST /api/weweb/login`
  - `POST /api/weweb/refresh`
  - `POST /api/weweb/logout`
  - `GET /api/weweb/me`
  - `GET /api/weweb/smoke`
  - `POST /api/weweb/admin/reset-owner-password`

## Runtime/Auth Model
- JWT bearer auth.
- Process-local revoked-JTI set used for explicit logout/refresh token retirement.
- Logout is explicit revocation for current token identifier.

## Local vs Live Contract Truth
- Local canonical OpenAPI includes `/api/weweb/logout`.
- Live production OpenAPI currently does not include `/api/weweb/logout`.
- This is a deployment parity issue, not a frontend trigger issue.

## Test Truth (This Checkpoint)
- Focused backend tests for logout contract pass locally.
- WeWeb runtime proved fail-closed auth behavior and logout trigger wiring.

## Shadow Mode Truth (2026-10-07)
- Canonical shadow enforcement now blocks real-world side effects through engine guard enforcement in direct dispatch paths.
- New block audit event: `shadow_action_blocked` (legacy `autonomy_action_blocked` retained for compatibility).
- Hardened paths now explicitly guarded before any external call attempt:
  - Notification dispatch job (email + webhook)
  - Contract send-for-signature pipeline
  - Direct DocuSign adapter send
  - Direct Stripe payout adapter
  - Direct QuickBooks journal-post adapter
- Completion registry source governance expanded with rights/license/trust/provenance/freshness/shadow-approval fields.
- New real-data rehearsal endpoint: `POST /api/completion/shadow/rehearsal/winnipeg` (public-data read only; no outreach/payment effects).

## Shadow Certification Truth (2026-10-08)
- Certification matrix executed with evidence artifact `docs/_shadow_certification_evidence.json`.
- Matrix status: 29 passed, 0 failed.
- Blocked action attempts: 23.
- `shadow_action_blocked` payload required metadata keys present (`timestamp`, `actor`, `legacy`, `policy_mode`, `provider`, `correlation_id`, `work_item_id`).
- Zero external effects counters recorded as 0 for email, SMS, calls, contracts, e-sign, payouts, accounting writes, external posts.

## Real Data Rehearsal Truth (2026-10-08)
- Rehearsal evidence artifact: `docs/_shadow_winnipeg_rehearsal_evidence.json`.
- Run1: fetched 20, inserted 20, duplicates 0, blocked 0.
- Run2: fetched 20, inserted 0, duplicates 20, blocked 0.
- Live-mode attempt correctly rejected with 409.
- Persisted 20 real public records from Winnipeg/Open Canada sources with citations and governance metadata.
- Explicit insufficiency statuses now emitted in rehearsal output and evidence:
  - VALUATION_CONFIDENCE_LOW
  - BUYER_DATA_INSUFFICIENT
  - CONTACT_NOT_VERIFIED
- Run1 insufficiency counts: 20 / 20 / 20.
- Run1 pending review count: 20 (`PENDING_HUMAN_REVIEW` represented through `review_status=PENDING_HUMAN_REVIEW` on inserted records).
- Run1 parse/source counters: parse_failures=0, source_failures=0, rejected=0.

## Remaining Truthful Gaps
- Full backend regression remains PARTIAL due unrelated suite blockers outside shadow-control paths.
- Broad suite triage artifact (`docs/_broad_regression_classification.json`) shows:
  - Introduced by shadow work: 0
  - Pre-existing unrelated: 84
  - Environment dependency: 13
  - Test harness defects: 59
  - Unknown: 0

## Winnipeg Certification Reproducibility Truth (2026-10-10)
- Prior clean-state failure cause was dependency on developer-local `valhalla_local.db` fallback rows when canonical CSV anchors were fewer than route minimum.
- Test harness now seeds deterministic Winnipeg fixture anchors in test setup for `test_phase2_winnipeg_certification_route_returns_rankings_and_shadow_safety`.
- Reproducibility evidence artifacts:
  - `docs/WINNIPEG_TEST_FIXTURE_CERTIFICATION.md`
  - `docs/_winnipeg_test_fixture_certification.json`
- Production thresholds and runtime Winnipeg logic were not lowered or relaxed.
- Certification boundary is explicit:
  - `TEST_FIXTURE_CERTIFICATION` proves deterministic route/path behavior.
  - `REAL_DATA_CERTIFICATION` proves behavior against current real Winnipeg source data.

## Canonical Phase Three Promotion Truth (2026-10-10)
- Canonical merge to `origin/main` completed from certified candidate branch `promote/phase3-blocker-repair-candidate-v3`.
- Promotion merge commit: `f89cf246a8e193fecb8717c5bc41e4e9b6b5c839`.
- Clean-checkout post-push validation passed for:
  - focused Phase Three suite (`58 passed, 0 failed, 0 errors, 0 skipped`)
  - Winnipeg fresh-database certification route
  - Phase Two regression slice (Pantheon/roles/Winnipeg/legacy orchestration/shadow safety)
- Broad backend gate remains a collect-only parity gate at this stage:
  - collection interrupted with 9 existing collection errors on both baseline and promoted main
  - introduced collection regressions: 0
- Canonical certification boundary remains mandatory:
  - `TEST_FIXTURE_CERTIFICATION != REAL_DATA_CERTIFICATION`

## Backend Test Baseline Hardening Truth (2026-10-10)
- Hardening branch: `hardening/backend-test-baseline` from canonical main `93cb1afe8d7fbbc01385ea54d5fa992647be647b`.
- Collection baseline restored from `9` errors to `0` errors.
- Current collected test count: `913`.
- Unexpected local modification classification:
  - File: `services/api/app/services/audit_service.py`
  - Classification: `REQUIRED_HARDENING_FIX`
  - Scope: compatibility wrapper for legacy integrity tests (`AuditService.log_event` -> `log_audit_event`), no business-rule or router behavior change.
  - A/B proof: reverting this file to HEAD content reintroduces `ImportError: cannot import name 'AuditService'` for `services/api/tests/test_system_integrity.py` collection.
- Required regression protections remain PROVEN on this branch:
  - Phase Three focused suite: `58 passed, 0 failed, 0 errors, 0 skipped`
  - Phase Two regression slice: `PASS`
  - Winnipeg fresh DB reproducibility: `PASS`
  - Shadow safety lane: `PASS`
- Full-suite reproducibility (fresh DB runs):
  - Run A: `913 total / 242 passed / 465 failed / 188 errors / 18 skipped`
  - Run B: `913 total / 242 passed / 465 failed / 188 errors / 18 skipped`
  - Reproducible full-suite outcome: `YES`
- Remaining failure families are documented without suppression:
  - `TEST_HARNESS_DEFECT`: 295
  - `TEST_DATA_DEFECT`: 8
  - `ENVIRONMENT_DEFECT`: 13
  - `ACTUAL_PRODUCTION_DEFECT`: 73
  - `EXPECTED_EXTERNAL_DEPENDENCY`: 0
  - `UNKNOWN`: 264