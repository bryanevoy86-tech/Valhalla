# FRONTEND BLOCKERS

Generated: 2026-09-28

## Active Blocker
- ID: AUTH-LOGOUT-PROD-PARITY
- Class: EXTERNALLY BLOCKED - SPECIFIC REASON
- Description: Live production OpenAPI does not expose `POST /api/weweb/logout`.

## Evidence
- Local canonical OpenAPI includes `/api/weweb/logout`.
- Live production OpenAPI includes:
  - `/api/weweb/login`
  - `/api/weweb/me`
  - `/api/weweb/smoke`
  - `/api/weweb/admin/reset-owner-password`
- Live production OpenAPI currently excludes:
  - `/api/weweb/logout`
  - `/api/weweb/refresh`

## Impact
- Backend logout call returns 404 in production.
- Frontend still fail-closes safely, but contract parity is incomplete.

## Unblock Condition
- Deploy backend revision that includes auth_weweb logout/refresh routes.
- Verify live OpenAPI and runtime chain end-to-end.