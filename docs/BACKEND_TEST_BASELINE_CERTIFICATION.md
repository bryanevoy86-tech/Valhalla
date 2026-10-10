# BACKEND TEST BASELINE CERTIFICATION

Generated: 2026-10-10
Branch: hardening/backend-test-baseline
Canonical main reference: 93cb1afe8d7fbbc01385ea54d5fa992647be647b

## Objective
Restore a trustworthy canonical backend regression baseline by eliminating pre-existing test collection blockers, preserving certified Phase Two/Phase Three behavior, and reporting full-suite reality without masking failures.

## Collection Baseline
- Original collection errors: 9
- Final collection errors: 0
- Total tests collected: 913

## Root Causes Repaired (Collection Gate)
- Stale legacy import paths in tests referencing non-canonical packages (`backend`, `valhalla`, `backend.app`).
- Missing compatibility exports expected by legacy integrity tests (`Base`, alias models) in app model package init.
- Stale/removed owner-command dependency in fake-live harness tests.
- Pydantic date annotation collision causing unevaluable type annotation in `pack_sz_ta_tb` schema.
- Legacy integrity tests importing `AuditService` symbol no longer present in canonical service module.

## Unexpected Local Modification Resolution
File: services/api/app/services/audit_service.py

Classification: REQUIRED_HARDENING_FIX

Provenance evidence:
- Change was introduced during this hardening session via explicit patch to restore legacy integrity test compatibility.
- HEAD and origin/main have no `AuditService` class in this file; working-tree change is local and intentional.
- A/B collection proof:
  - With HEAD version of file: `ImportError: cannot import name 'AuditService'` while collecting `services/api/tests/test_system_integrity.py`.
  - With hardening working copy: targeted collection passes.

Impact assessment:
- Imports changed: no.
- Existing function behavior changed: no (`log_audit_event` unchanged).
- Added API surface: yes (`AuditService.log_event` wrapper that delegates to `log_audit_event`).
- Test-only effect: YES.
- Production runtime effect: NO (no router wiring or business-rule path changes).

## Required Regression Protection
- Phase Three focused suite (`services/api/tests/test_completion_registry.py`):
  - 58 tests, 58 passed, 0 failed, 0 errors, 0 skipped
- Phase Two regression slice (Winnipeg/Pantheon/roles/legacy orchestration/shadow lanes): PASS
- Winnipeg fresh DB targeted reproducibility: PASS
- Shadow safety lane (`phase2_winnipeg_certification_route_returns_rankings_and_shadow_safety`): PASS

## Full Backend Metrics (Fresh DB)
Run A:
- Total: 913
- Passed: 242
- Failed: 465
- Errors: 188
- Skipped: 18

Run B:
- Total: 913
- Passed: 242
- Failed: 465
- Errors: 188
- Skipped: 18

Reproducible full-suite outcome: YES

## Remaining Failure Families (Truthful Classification)
- TEST_HARNESS_DEFECT: 295
  - Examples: stale legacy module paths; missing legacy symbols; route expectation mismatches from historical harness assumptions.
- TEST_DATA_DEFECT: 8
  - Example: LeadCreate validation payload mismatches.
- ENVIRONMENT_DEFECT: 13
  - Example: `httpx.ConnectError`/connection refused for tests expecting external listener behavior.
- ACTUAL_PRODUCTION_DEFECT: 73
  - Example: SQLAlchemy mapper init conflict (`TrustEventLog` duplicate path registration), plus runtime-key assumptions.
- UNKNOWN: 264
  - Requires deeper family-by-family triage; not hidden or reclassified without evidence.
- EXPECTED_EXTERNAL_DEPENDENCY: 0

## Integrity Statement
This hardening checkpoint intentionally does not force full-green status by weakening tests or bypassing failures. It establishes a reproducible, truthful baseline where collection is clean and required certified regressions are preserved.
