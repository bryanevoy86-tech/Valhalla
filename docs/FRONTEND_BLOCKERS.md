# FRONTEND BLOCKERS

Generated: 2026-09-30

## Active Blockers

### WEWEB_MCP_EDIT_AUTH_REQUIRED
- Status: EXTERNAL_OWNER_ACTION_REQUIRED
- Missing requirement: authenticated WeWeb MCP project-edit access for the Valhalla project
- Why incomplete: backend endpoints are ready, but real project mutation is blocked without live edit authorization
- Owner vs code responsibility: owner/auth responsibility
- Specific next action: sign into WeWeb MCP in this runtime and grant project edit scope
- Launch-blocking: YES
- Dependency: WeWeb MCP account/session authorization
- Evidence: contracts/weweb_sync_state.json

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
- WeWeb MCP authenticated project-edit access
