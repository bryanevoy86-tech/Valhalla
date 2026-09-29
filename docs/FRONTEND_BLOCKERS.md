# FRONTEND BLOCKERS

Generated: 2026-09-28

## Active Blocker
- ID: PRODUCTION_AUTH_CREDENTIAL_REQUIRED
- Class: EXTERNAL_OWNER_ACTION_REQUIRED
- Description: Full live authenticated chain and WeWeb Preview auth verification require secure credential execution.

## Evidence
- Live production OpenAPI includes:
  - `/api/weweb/login`
  - `/api/weweb/me`
  - `/api/weweb/logout`
  - `/api/weweb/refresh`
  - `/api/weweb/smoke`
  - `/api/weweb/admin/reset-owner-password`
- Live deployment identity still reports:
  - `/deployment-marker`: env-derived commit `9cc0dc4324a4940e3e748e0b31ebc20f8096486e`
  - `/admin/build/info`: matching env-derived `git_sha`

## Impact
- Auth route contract and deployment parity are now available in production.
- Remaining gap is secure execution of full authenticated proof chain.

## Latest Verification
- Source with `/api/weweb/logout` and `/api/weweb/refresh` is on `origin/main` at commit `de64555`.
- Live runtime probe confirms both routes are present in `GET /openapi.json`.
- Live runtime now reports parity commit `9cc0dc4` through both identity endpoints.

## Commit Parity Snapshot
- EXPECTED_COMMIT: `9cc0dc4324a4940e3e748e0b31ebc20f8096486e`
- LIVE_COMMIT_OR_BUILD: `9cc0dc4324a4940e3e748e0b31ebc20f8096486e`
- MATCH: `YES`
- CAUSE_IF_KNOWN: N/A

## Unblock Condition
- Execute secure production login chain and WeWeb Preview parity checks.
- Record PASS/FAIL evidence for login -> me -> refresh -> logout -> post-logout persistence.