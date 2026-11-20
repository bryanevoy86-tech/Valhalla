# Valhalla / Heimdall — Persistent Change Ledger

Maintained by: ChatGPT-assisted development; Git commits and PR diffs are authoritative.
Date: 2026-11-19 (UTC).
Canonical branch: fix/fail-closed-operations-20261119.
Review PR: https://github.com/bryanevoy86-tech/Valhalla/pull/4
Production main: unchanged by all commits listed below.

## Rules

Log every GitHub branch/commit/file, Render service/configuration/deployment mutation, CI result and live outcome. Recorded, tested, deployed and verified are different states. Nothing is DONE without applicable independent acceptance evidence. Never store secrets in this file.

## GitHub changes — 2026-11-19 (development branch only)

| Commit | File / action | Purpose | Verification |
|---|---|---|---|
| c28062b5 | services/api/app/scheduler/runner.py | Stop reporting placeholder clone deploys completed | Focused CI passed |
| ee4908bf | services/api/app/workers/outbox_dispatcher.py | Stop marking unsent messages dispatched | Focused CI passed |
| dca736a7 | services/api/app/cron/daily_ops.py | Stop claiming unimplemented payment, contract and alert success | Focused CI passed |
| ed5b1466 | services/api/app/jobs/runner.py | Require evidence to classify cron work successful | Focused CI passed |
| 80f8609b | services/api/app/heimdall/readiness.py | Replace hardcoded positive readiness with fail-closed gates | Focused CI passed |
| 4c6ea49c | tests/test_fail_closed_smoke.py | Add five false-success regression tests | 5/5 passed |
| 8984b2b2 | .github/workflows/critical-controls-ci.yml | Enable checks on pull requests | Actions run 44630305972 passed |
| a9886159 | services/api/app/services/prime_business_execution.py | Owner-gated durable internal draft task, receipt and idempotency | Integrated CI pending/result tracked in PR |
| 088081d4 | services/api/app/routers/prime_business_factory.py | Authenticated Product Foundry pilot endpoints | Integrated CI pending/result tracked in PR |
| 012c3eb1 | tests/test_business_factory_pilot.py | Exercise FastAPI + SQLite, approval, tamper and receipt lifecycle | Integrated CI pending/result tracked in PR |
| 1e17d6fa | .github/workflows/critical-controls-ci.yml | Add integrated test job using real FastAPI and SQLAlchemy | Integrated CI pending/result tracked in PR |

PR #4 was created in draft state. No merge, live deployment, or production schema changes have occurred.

Initial CI proof: https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44630305972
Five targeted tests and syntax checks passed. This does NOT certify the complete Business Factory.

New pilot execution scope: an INTERNAL digital-product listing draft is persisted into existing media_contents with a checksum receipt recorded in legacy_orchestration_events. Its task is stored in legacy_instance_work_items. Only this internal operation can be reported completed, not an external sale, delivered product, customer or published storefront.

Pilot API after deployment and secure VALHALLA_FACTORY_KEY configuration:
- POST /api/business-factory/listing-drafts (queue idempotent task).
- POST /api/business-factory/actions/{action_id}/approve (owner approval).
- POST /api/business-factory/actions/run-once (write one actual approved database artifact and receipt).
- GET /api/business-factory/actions/{action_id} (verify retained artifact integrity).

No production AI model calls, external messages, payments or new resource purchases are performed by this draft-only code.

## Render inspections and changes — 2026-11-19

**Render mutations performed: ZERO.** Inspections were read-only. This branch is not deployed.

Workspace: tea-d3fbf3r3fgac73b3ed40.
- API Valhalla-api, srv-d3hatinfte5s73cqbbh0: live deploy at Git commit 93cb1afe, October 10, 2026.
- Cron valhalla-daily-email, crn-d5u469npm1nc73d9n350: recent Nov 12–19 runs successful, endpoint HTTP 200, but it is NOT a Business Factory executor.
- Database valhalla db-v2, dpg-d90l1mv7f7vs73cod580-a: 0 public tables.
- Database valhalla db-v2-copy, dpg-d9ek3oj7uimc73fooes0-a: 367 public tables.
- Exact production API database connection not verified; do not delete or change databases by guessing.

Do not log Render secrets or connection strings. A future Render mutation entry MUST include resource name/id, action, approved purpose, source commit/deploy ID, verification and rollback/containment decision.

## External and technical blockers

- No seller/payment processor account or real storefront authorization verified.
- No independent proof of a running always-on Business Factory worker.
- No proof of full-suite backend test collection health or live production business execution.
- No owner factory key configured on Render by these changes.
- No demonstrated real marketing publication, buyer acquisition, receipt, or cash reconciliation.
- Cannot directly control the user's existing local VS Code Codex session from this chat.
- More integration tests, review and authorization required before merging or deploying.

## Future updates

Append dated entries, never rewrite historical claims. Each entry must state files, commit SHA, PR, tests, Render actions (or NO CHANGES), exact verified outcome and remaining blockers.


## Follow-on GitHub work — 2026-11-19

| Commit | File / action | Outcome |
|---|---|---|
| 54c59bc3 | ops/CHANGE_LEDGER.md | Established this persistent change ledger |
| d216c660 | docs/HEIMDALL_DEFINITION_OF_DONE.md | Documented cross-industry Prime architecture and strict proof stages |
| 4e175e79 | docs/CODEX_RESUME_2026-12-01.md | Added exact future VS Code Codex branch-fetch and integration prompt |
| 0e326e14 | services/api/tools/cron/business_factory_tick.py | Added disabled-by-default HTTPS/host-restricted worker tick; no paid service created |
| d6cc61b9 | services/api/tools/cron/daily_email_ping.py | After email success, optionally invoke restricted worker tick; missing config = skip |
| bb1930da | tests/test_business_factory_cron.py | Verify no token exposure, no redirect to unauthorized host, and no fake success |
| d70f886e | .github/workflows/critical-controls-ci.yml | Added cron test + syntax checks |
| 8bd648e0 | services/api/app/routers/prime_business_factory.py | Return HTTP 503 if required persistent schema missing; do not create tables during API requests |
| 1e03ddf6 | alembic/versions/20261119_factory_legacy_work_schema.py | Add schema preparation following existing 20261007 governance migration; preserve legacy data |
| 2eb3ace5 | services/api/app/services/prime_business_execution.py | Harden idempotency across engine, industry, jurisdiction and business scope |
| 35fc506f | tests/test_business_factory_pilot.py | Test schema missing and cross-scope idempotency denial |
| b00eb290 | tests/test_factory_migration.py | Test non-destructive, repeatable migration in disposable SQLite |
| 9cc0d4d6 | .github/workflows/critical-controls-ci.yml | Run real Alembic migration tests |
| 70c7bb88 | docs/CODEX_RESUME_2026-12-01.md | Added schema and cron handoff facts |

### Latest confirmed CI result

**2026-11-19, GitHub Actions run 44637143438: SUCCESS**
https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44637143438

- False-success prevention suite: 5 passed.
- Real FastAPI + disposable SQLite Business Factory lifecycle: 7 passed.
- Disabled-by-default cron/HTTPS/secret tests: 6 passed.
- Non-destructive Alembic upgrade tests: 2 passed.
- Total **20 passed**, no failures in the **targeted suites**.
- Python syntax check passed.
- FULL backend suite and actual Render PostgreSQL operation NOT certified.

### Additional Render read-only inspection

Render DB dpg-d9ek3oj7uimc73fooes0-a:
- public tables include media_contents, media_channels and alembic_version;
- missing legacy_instance_work_items, legacy_instance_registry_items and legacy_orchestration_events;
- alembic_version reports 8e43f380be7f;
- GitHub contains an existing next revision 20261007_shadow_source_governance.
- API source Dockerfile launches services/api/start.py, which documents external pre-deploy migrations; current Render web service pre-deploy command was observed empty.
- Therefore the new pilot intentionally refuses production requests with HTTP 503 until schema prepared.

**Render mutations remain ZERO.** No migration applied, worker activated, credentials configured or new service created. Existing live main commit remains unchanged.

### Release and owner handoff

- Current PR contains 18 changed files, all tracked in the PR diff and this ledger.
- Branch remains fix/fail-closed-operations-20261119 and PR #4 remains draft.
- No actual commerce, payments, storefront publication, or customer marketing is claimed.
- A safe approval-controlled release requires validating the true database connection, rehearsing migrations on a disposable copy, reviewing auth and full backend suite, preparing a rollback/containment plan, setting secrets in the authorized provider, merging a reviewed PR and verifying live behavior.
- On Codex resumption: fetch the development branch; read docs/CODEX_RESUME_2026-12-01.md before additional coding.


## Final review metadata update — 2026-11-19

- PR #4 title/body updated to reflect the full 18-file scope, the 20 passing focused/integration tests, migration and optional cron wiring, and explicit deployment blockers.
- Link: https://github.com/bryanevoy86-tech/Valhalla/pull/4
- This metadata change does not modify application code.
- Render mutations: NONE. Live production remained unchanged.


## System-wide readiness and safety preparation — 2026-11-19 evening

**Scope:** continuation of draft PR #4 on branch fix/fail-closed-operations-20261119. No direct main pushes.

| Commit | Change | Evidence level |
|---|---|---|
| e47ed6cd | core/builder_path_policy.py: reject path traversal, absolute paths, symlink escapes and paths outside allowlist | Focused tests |
| f873bc75 | routers/builder.py: safe repo-root writes, atomic writes and digests, disallow API direct-Git push | Syntax + path tests; full builder integration not yet verified |
| 749d27f8 | tests/test_builder_path_security.py: 7 path/security cases | Targeted CI pass |
| 2f503573 | providers/stripe_adapter.py: proper timestamped Stripe-Signature HMAC v1 verification | Targeted CI pass |
| 9676e3f2 | webhooks/stripe.py: no unsigned event acceptance or false success, 503 until real ledger handler | Targeted CI pass; not a functional payment consumer |
| 18d19eb0 | integrations/stripe/payouts.py: no fabricated payout id or false "in_transit" status | Targeted CI pass; no real transfer implementation |
| 54e07b09 | services/media_engine.py: reject unsupported "published" status | Integration tests pass |
| 935aa316 | services/marketing_service.py: reject unsupported external publication status | Integration tests pass |
| a71b9de1 | routers/marketing.py: mount existing campaign registry behind Builder owner key | Integration tests pass |
| 400e01c7 | routers/media_engine.py: require owner key for media records | Integration tests pass |
| 876669b7 | tests/test_prime_finance_safety.py: verify signed/invalid/replay Stripe and fake payout prevention | Targeted CI pass |
| 1de4f79d | tests/test_prime_publication_safety.py: FastAPI/SQLite owner and no-fake-publication tests | Targeted CI pass |
| c763d290 | ops/prime_system_integration_matrix.json: 25 anchored capability contracts with dependencies and exact acceptance tests | Source preflight passed; not live proof |
| 9840b44c | scripts/prime_system_preflight.py: static source/AST integrity and proof-stage inflation checker | Targeted CI pass |
| 83646762 | tests/test_prime_system_preflight.py: prevent false live declarations and broken source dependencies | Targeted CI pass |
| 7c90da0a | CI workflow expanded across Builder, media, marketing, finance and system inventory | Actions run 44652014397 success |
| f8dfdf03 | core/route_integrity.py: required critical router set and missing-import evidence | Focused tests |
| 599479d2 | app/main.py: track critical router import failures, avoid deceptive health label, readiness fails when missing | Focused tests; full main import not yet proven |
| 24941aca | tests/test_route_integrity.py: detect missing critical routers even with many optional routers | Targeted CI pass |
| cc64d0e0 | app/main.py: default /readyz DB + worker checks, use SQLAlchemy 2 text() | Syntax, focused checks; live behavior not yet proven |
| 7c917a0f | CI workflow: route integrity check and compilation | Targeted CI pass |
| bedc3ac6 | core/dependencies.py: legacy session auth fails closed by default; constant-time key comparisons, explicit DEV-only override | Targeted CI pass |
| 7f3e3968 | tests/test_core_auth_contracts.py: missing secret, dev-only, invalid key and success cases | Targeted CI pass |
| ae5ff5f4 | CI workflow: include legacy auth checks | Actions run 44652624533 success |
| a7dbec40 | docs/CODEX_SYSTEM_FINISH_PASSES.md: three rigorous Codex prompts for all 25 domains | Recorded scope, not software completion |

### CI proof for expanded system controls

- Earlier 40-test run (Builder path, Stripe, marketing, media, factory, migration, static system preflight): https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44652014397
- Latest 49-test run (adds 5 critical router tests and 4 legacy auth tests): https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44652624533
- All 49 targeted tests passed. THIS IS NOT the canonical full backend suite, live PostgreSQL proof, production deployment or real customer transaction.
- Machine preflight: 25 source-anchored domains, no missing static anchors, zero domain-level production verified declarations.

### Real cross-domain issues identified for December

- Main router loader previously swallowed failed imports, leaving apparently healthy endpoints; new branch records missing mandatory imports and makes /readyz red. Live route parity remains untested.
- WeWeb logout uses a process-local revoked-JTI set; restart and multi-instance authentication tests remain.
- Research service includes in-memory source registration, while scripts contain richer ingestion; automatic durable discovery loop needs integration.
- Heimdall outcomes include a local JSON path; lasting Mimir outcome learning and replay feedback need integration and durable evidence.
- Builder prior allowed path traversal and automatic direct Git pushes; new branch blocks these, but safe PR/code-builder autonomy remains to be implemented.
- Stripe webhook used an invalid illustrative signature check and claimed events recorded; new branch verifies genuine signatures but deliberately returns 503 for financial events until ledger consumption exists.
- Stripe payout path previously fabricated a provider payout id. New branch blocks unimplemented live payouts.
- Social post and media records could claim publication without actual provider interaction; now blocked. Real platform publishing still missing.
- Legacy marketing router was outside the current app.routers autoload and has now been mounted under owner auth.
- Historical core dependency require_auth allowed no-token operation when no token was configured; new branch defaults to fail closed.
- Live Render db-v2-copy is missing legacy orchestration tables, and factory migration is not applied. Exact API database link still unverified.
- Full backend test collection previously had 9 existing collection errors; no new system-wide clean result has been established.

### Render mutation log for this phase

**NONE.** No new service, environment variable, database alteration, deploy, schema migration, payment, outreach or cron activation was initiated. This is GitHub-only preparation for review and Codex handoff.

### Reviewer obligations

- Review diff for backward compatibility and side effects of the stricter auth, published-state and readiness gates before any merge.
- The media/marketing/finance changes are deliberately incomplete provider adapters; never mislabel them "finished business".
- Never enter provider secrets or tokens in GitHub files.
- Run full-suite tests and actual Postgres migration rehearsal; resolve false health and process-local state before activating automatic workflows.
