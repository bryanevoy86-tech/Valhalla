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