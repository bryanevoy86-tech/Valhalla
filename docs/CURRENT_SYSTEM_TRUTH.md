# CURRENT SYSTEM TRUTH

Generated: 2026-09-28

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