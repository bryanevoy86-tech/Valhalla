# CODEX START HERE — Heimdall Prime integration (December 2026)

This is the one-file handoff from ChatGPT's November 19 development and audit. **Do not create new packs or restart Valhalla.**

## Existing project

- Repo: https://github.com/bryanevoy86-tech/Valhalla
- Production: main, automatically deploys to Render.
- Continue work from branch: fix/fail-closed-operations-20261119
- Review draft: https://github.com/bryanevoy86-tech/Valhalla/pull/4
- Live production and Render have NOT been mutated by this branch.

## Read in this exact order

1. ops/CHANGE_LEDGER.md (every development change, CI evidence, ZERO Render mutations).
2. ops/REMAINING_SYSTEM_BLOCKERS_2026-11-19.md (new cross-source log review and current blockers).
3. ops/prime_system_integration_matrix.json (25 actual capability anchors, open acceptance conditions).
4. docs/HEIMDALL_DEFINITION_OF_DONE.md (no more "finished" placeholders).
5. docs/CODEX_SYSTEM_FINISH_PASSES.md (the **three** ordered Codex work packages).
6. docs/CODEX_RESUME_2026-12-01.md (local Git commands, Render facts and current blockers).
7. docs/PHASE3_INTEGRATED_ARCHITECTURE.md (canonical Prime opportunity pipeline).

## Important verified code already committed

- A real owner-approved, database-backed internal Digital Products draft action and checked SHA-256 receipt.
- Non-destructive Alembic preparation for missing orchestration work tables.
- Optional safe Business Factory cron tick, inactive unless deliberately configured.
- Builder source-path allowlist security and no API direct push to main.
- Correct Stripe-Signature v1 verification, no invented payment or payout success.
- Marketing/media owner-key protection and no fabricated published status.
- Fail-closed legacy session API key when no secret is configured, dev bypass explicit.
- Critical-router import integrity and readiness that do not silently claim modules are loaded.
- Machine preflight for 25 Prime domains and regression tests.
- Canonical FastAPI route probe (scripts/prime_runtime_route_probe.py) to run in an isolated Codex environment with --import-app --json; its own contract tests pass, but full backend imports are not yet certified.
- 85 targeted tests passed: https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44658342650 (47 smoke + 35 SQLite integration + 3 disposable PostgreSQL)
- Full backend regression, live PostgreSQL and real-world business outcomes NOT yet proven.

## Single prompt to give Codex

Continue my EXISTING Heimdall Prime / Valhalla system; do not start over. First preserve any local-only changes, then fetch origin/fix/fail-closed-operations-20261119, review its draft PR #4, and read CODEX_START_HERE.md, ops/CHANGE_LEDGER.md, ops/prime_system_integration_matrix.json, docs/HEIMDALL_DEFINITION_OF_DONE.md, and docs/CODEX_SYSTEM_FINISH_PASSES.md. Execute the three ordered integration passes against current source code, beginning with canonical full-app import, full regression tests, PostgreSQL migration rehearsal, secure identity, durable workers and evidence receipts. Repair the missing connections across the complete private Heimdall Prime, general discovery/decision/Mimir learning, five legacy businesses, Product Foundry and independently operating Venture Foundry. Reuse existing modules; no new pack scaffolds. Each claimed completed operation must have actual execution and independent proof. Keep all changes in GitHub review branches and record file changes, SHAs, CI results, unresolved dependencies and any Render action in ops/CHANGE_LEDGER.md. Never force-push, publish customer material, spend money, transfer funds, change external accounts or deploy production without my specific authorization. Once each pass is tested, give me the exact remaining gaps and an evidenced next step, not an optimistic completion percentage.

## Absolute boundaries

- Heimdall Prime is strictly private to the owner.
- Only approved subordinate systems may become externally sold subscription products.
- An internally stored product/media draft is not a published product or paid order.
- No provider funds, outreach or legal operations may occur from unapproved authority.
- A green CI run is not live production success.
- Do not guess which Postgres database the live API uses.
- No direct main commit before a reviewed, explicit deployment approval.


## Added: Autonomous risk-control governor

Read docs/PRIME_AUTONOMY_SAFETY_CONTRACT.md. New deterministic autonomy risk governor: services/api/app/core/autonomy_governor.py, integrated into services/api/app/services/prime_business_execution.py. It checks trusted owner approval, scope, cost, source evidence, circuit breaker, uncertain outcomes and emergency stop. External/provider actions remain review or blocked; only internal approved draft is actually wired. Test cases in tests/test_autonomy_governor.py and tests/test_business_factory_pilot.py.

Latest targeted CI: https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44654950056 — 71 passed. NOT proof of broad backend production behavior. Codex must wire external action guards from trusted DB records to every provider, and show independent provider receipts with full integration/staging tests.


## Confirmed progress from latest log audit

- The canonical app actually imported on isolated Linux CI with all seven designated critical routers and nine required endpoints registered. This is now a required CI gate, not a synthetic list.
- Database driver initialization is fail-closed; owner recovery always requires a setup secret. WeWeb logout/refresh revocation is persistent in database (new additive migration pending release).
- Factory executes one owner-approved internal draft, records SHA-256 receipt and survived fresh PostgreSQL session + simultaneous two-worker attempts in disposable CI.
- Factory and revocation schema changes are repeatable on disposable PostgreSQL; production data and full migration chain are NOT verified.
- Backend test collection is still a diagnostic, with two legacy import errors (missing system_self_check and outdated system_integrity models). See ops/REMAINING_SYSTEM_BLOCKERS_2026-11-19.md.
- Render production remains untouched. API/cron log sweeps found no error/5xx entries in queried windows; live API still runs October 10 commit.

**Critical:** Read the new log triage file before attempting to merge/release. No credentials and no real provider effects are part of the isolated tests.
