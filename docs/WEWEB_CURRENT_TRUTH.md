# WEWEB CURRENT TRUTH

Generated: 2026-10-04

## Live Editor Access
- PASS: authenticated access to the real WeWeb project is available.
- Project: Valhalla Legacy INC.
- Editor URL: https://286b2f26-c8e6-4561-ac4b-ca6537e7f8fe-editor.weweb.io/

## Authentication Architecture (Audited Live)
- Custom backend/API auth is implemented in workflows and variables.
- WeWeb native auth integration is not selected in this project (`No auth system selected`).
- This is expected when using custom FastAPI auth flows and is not itself a regression.

Verified workflow evidence:
- `handleLogin` reads credentials, calls `/api/weweb/login`, validates owner via `/api/weweb/me`, sets auth state (`AUTH_TOKEN`, `CURRENT_USER`, `IS_LOGGED_IN`), and fail-closes on errors.
- `handleLogout` attempts `/api/weweb/logout`, then always clears local auth/session state and returns to login view.
- App bootstrap includes auth guard trigger.

## Surface Inventory Observed In Live Project
- Primary pages visible: Home, Login, Deals, Lead Intake, Reports EIA, System Status.
- Additional draft/accidental pages exist (marked with `ACCIDENTAL_DO_NOT_USE` naming) and are not publish targets.
- Variables and workflow groups for auth/api/deals/reports/system-status/va flows are present.

## Current Classification
- Auth implementation pattern: PASS (custom contract-preserving flow present).
- Launch-facing Heimdall cockpit completeness: PARTIAL.

## Remaining Gaps To Close For Launch-Facing UI
- Learning status/curriculum/mastery live surfaces.
- Evidence and re-verification operational queues.
- Continuous integrity and autonomy/shield/kill owner surfaces.
- Engine registry and legacy control center owner-facing cockpit views.
- External owner checklist page status surface.

## Proof Boundaries In This Session
- Live editor wiring and workflow evidence are verified.
- Full credentialed preview chain re-proof in this session (login/refresh/logout/post-logout guard) remains pending until credentials are executed in preview test steps.