# WEWEB CURRENT TRUTH

Generated: 2026-09-28

## Proven In Preview Runtime
- Owner login executes and succeeds.
- `/api/weweb/me` identity fetch succeeds.
- Refresh preserves authenticated state.
- Sign out control is correctly wired and triggers logout workflow.
- Client auth variables clear and app returns to login view.
- Post-logout refresh remains fail-closed on login.

## Not Proven Live Yet
- Successful non-404 backend response for `POST /api/weweb/logout` in production.

## Active Boundary
- Frontend behavior is fail-closed and correctly wired.
- Remaining defect is backend production contract parity for logout endpoint.