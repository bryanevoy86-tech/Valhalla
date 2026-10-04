# FRONTEND BLOCKERS

Generated: 2026-10-04

## Active Blockers

### WEWEB_LAUNCH_SURFACES_INCOMPLETE
- Status: PARTIAL
- Missing requirement: complete and verify launch-facing Heimdall cockpit surfaces in the real project
- Why incomplete: access is now available and custom auth is implemented, but required learning/evidence/integrity/autonomy/engine/legacy owner views are not fully wired and proven
- Owner vs code responsibility: code/frontend wiring responsibility
- Specific next action: finish live API bindings and preview proof for each required launch-facing surface
- Launch-blocking: YES
- Dependency: live WeWeb build execution and verification
- Evidence: contracts/weweb_sync_state.json

Required launch-facing real-project screens to complete now:
- Learning Status
- Curriculum / Mastery visibility
- Re-verification Queue
- Evidence / Ethics status
- Autonomy State
- Continuous Integrity
- System Blockers
- Shield / Pause / Kill visibility
- Engine Registry / Readiness
- Legacy Instance Status
- Legacy Health
- Legacy Sync State
- Legacy Failover State
- Legacy Policy Version / Divergence alerts

Live evidence already confirmed:
- Real editor/project access is available.
- Custom auth workflow is present (`handleLogin`/`handleLogout`).
- Native WeWeb auth is intentionally not selected (`No auth system selected`).

### LEGACY_ORCHESTRATION_RUNTIME_PROOF
- Status: PASS
- Missing requirement: none for controlled launch baseline
- Why complete: backend now includes executable orchestration runtime with deterministic conflict/failover/recovery proof
- Owner vs code responsibility: code responsibility (closed for this milestone)
- Specific next action: continue scenario expansion as scale hardening, not a launch blocker
- Launch-blocking: NO
- Dependency: none
- Evidence: services/api/tests/test_completion_registry.py and docs/DECEMBER_FULL_LAUNCH_MATRIX.md

## External Launch Action List (Owner-Facing)
These are external actions, separate from software defects:
- Incorporation/entity finalization
- Lawyer review and sign-off
- Accountant setup and accounting policy sign-off
- Business bank account readiness
- Insurance binding
- Business email/domain setup
- SMS/voice provider account + verified sender
- E-sign provider account authorization
- Accounting provider credentials
- Google/business document storage authorization
- Lead-source credentials
- Buyer data access/authorization
