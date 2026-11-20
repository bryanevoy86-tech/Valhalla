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


## Canonical full-application route contract preparation — 2026-11-19 late evening

| Commit | Change | Proof |
|---|---|---|
| 19ab05ba | CODEX_START_HERE.md root handoff created, with one main Codex prompt | GitHub committed |
| 188f6410 | docs/CODEX_RESUME_2026-12-01.md expanded with 25-domain and security changes | GitHub committed |
| 9bea307e | scripts/prime_runtime_route_probe.py: exact HTTP route registration audit for canonical app; test environment only | Unit tested |
| 157bcb99 | tests/test_prime_runtime_route_probe.py: four method/route/absence/factual-scope tests | 4/4 passed |
| cd433985 | CI workflow expanded to include route probe syntax and contract tests | Targeted CI passed |
| 6c1b6f96 | CODEX_START_HERE.md updated to 53-test results and route probe | GitHub committed |
| 7801b245 | docs/CODEX_SYSTEM_FINISH_PASSES.md Pass 1 now requires isolated canonical runtime route import | GitHub committed |
| 6d370c33 | docs/CODEX_RESUME_2026-12-01.md updated to 53-test and route probe evidence | GitHub committed |

**Latest GitHub Actions evidence:** https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44653459058
- 53/53 targeted tests passed: initial false-success, Builder path security, signature/payout safeguards, marketing/media published-state, strict owner/session auth, route integrity, internal Factory/SQLite, migration, cron, source matrix, and route probe contract tests.
- The canonical app was NOT imported in this CI run. The new runtime route tool has only been tested against synthetic route lists. This is explicitly a December Pass 1 acceptance gate, not done.
- Preflight continues to show 25 source-anchored domains and ZERO claimed production-verified domains.

**GitHub PR metadata:** PR #4 remains draft; updated to include 25-domain contracts and system-wide safety boundaries, no merge. Codex should start from root CODEX_START_HERE.md on the same branch.

**Render mutations:** ZERO. No changes to services, schedules, databases, environment variables, deployment commits, billing or production data.

**Next mandatory acceptance:** full canonical FastAPI import and route registration, complete regression, actual PostgreSQL migration rehearsal, live worker/restart proof, provider-account and financial sandbox integrations, then explicit owner-approved production deployment and external proofs.


## Bounded autonomy safeguards — 2026-11-19

User asked how Heimdall can avoid AI hallucinations, harmful optimization, unexpected disruption and the need to micromanage routine business operations. These are **engineering risk controls**, not blanket declarations of fully autonomous business operation.

| Commit | File/action | Verification |
|---|---|---|
| 936bf404 | services/api/app/core/autonomy_governor.py: first deterministic risk policy (ALLOW/ABSTAIN/REVIEW_REQUIRED/BLOCK), scope, evidence, spending, circuit breaker, uncertainty, kill switch and shadow-mode checks | New targeted unit tests |
| 4dd457f5 | services/api/app/services/prime_business_execution.py: verify policy and existing go-live-state kill switch before a real internal artifact write; stamp receipt policy evidence | Integrated Factory tests |
| df615afe | tests/test_autonomy_governor.py: unit test branches for source uncertainty, injection, consent, disallowed payments, missing owner approval and outages | Targeted CI |
| 1096040f | tests/test_business_factory_pilot.py: additional emergency env and DB kill-switch tests | Integrated CI |
| a0b7bcbc | .github/workflows/critical-controls-ci.yml: run new policy tests | Targeted CI |
| d49a6e8a | core/autonomy_governor.py: tighten unverified system-integrity default to false | Fail-closed test |
| ee55cf3c | tests/test_autonomy_governor.py: assert default unverified state blocks | Targeted CI |
| ad75a60e | docs/PRIME_AUTONOMY_SAFETY_CONTRACT.md: original long-term risk model and bounded-autonomy acceptance criteria | Documentation |
| 6c5c66aa | ops/prime_system_integration_matrix.json: add governor to existing runtime governance source/acceptance contract | Static preflight CI |
| 490ae55c | CODEX_START_HERE.md: include autonomy governor and risk criteria | Handoff |
| 7b352cce | docs/CODEX_SYSTEM_FINISH_PASSES.md: add cross-system enforcement, durable circuit breakers and evidence as required work | Handoff |
| a3bdbd59 | docs/CODEX_RESUME_2026-12-01.md: current guard scope, live caveats and proof | Handoff |

**CI acceptance:** https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44654950056
Two jobs completed successfully: 47 smoke/policy/static tests + 24 SQLAlchemy/FastAPI/provider-boundary tests = **71 targeted tests passed**. Earlier transient intermediate commit had a failed run before the fail-closed-default correction; the later 71-test run is the verified passing state. Not a green broad suite, PostgreSQL concurrency, provider, or live deployment certification.

**Currently integrated:** new governor is checked by the approved INTERNAL_DRAFT_ONLY Business Factory worker; it reads trusted owner approval event, scoped legacy record and emergency stop before the write. It returns truthful blocked status and leaves the work queued when stop is engaged. Existing GoLiveState database kill-switch is supported when table exists. The missing-go-live-table fallback applies ONLY to internal/no-external-effect pilot.

**NOT integrated:** universal source/evaluation evidence verifier, external publishing, customer outreach, legal contracts, payments, payouts, production code deploy, persistent circuit breaker state, global multi-instance authorization, or owner notification/escalation. The pure governor does not magically secure external adapters that do not call it. Provider effect guards must be wired and tested at actual dispatch boundaries.

**Render:** ZERO mutation. No deployment, service, cron schedule, environment variable, database row or schema changed from this task. The production main branch remains unchanged.

## Final governance PR and production recheck — 2026-11-19

- PR #4 title and description updated to include deterministic autonomy governor, new tests, NIST/OWASP-inspired control objectives and explicit external-adapter limitations; remains DRAFT, not merged.
- Rechecked production Render API: still live on commit 93cb1afe8d7fbbc01385ea54d5fa992647be647b (October 10, 2026). The governance branch is NOT deployed.
- Confirmed GitHub Actions run 44654950056 completed SUCCESS with 71 targeted tests.
- Repo branch includes CODEX_START_HERE.md, docs/PRIME_AUTONOMY_SAFETY_CONTRACT.md and updated December handoffs.
- **Render mutations from this governance task: NONE.** No environment, credentials, database, cron, payment, or deployment modifications.


## Full log triage and integration preparation — 2026-11-19 (UTC CI: Nov 20)

Source inventory: ops/REMAINING_SYSTEM_BLOCKERS_2026-11-19.md. The following are all changes to the existing development branch; **Render mutation count remains ZERO**.

| Commit | File | Concrete change / effect |
|---|---|---|
| e1996b6d | services/api/app/routers/auth_weweb.py | Force a configured and matching X-Setup-Token on every enabled owner-password reset |
| 0c7ec0ef | tests/test_owner_reset_auth.py | Negative tests for disabled, missing secret, wrong secret and missing owner credentials |
| 249e0139 | services/api/app/core/db.py | Invalid DB engine or schema cannot silently fall back to in-memory SQLite |
| 71f51914 | tests/test_factory_postgres.py | Disposable PostgreSQL persistence/fresh-session and two-worker deduplication tests |
| 3f1f2675 | .github/workflows/critical-controls-ci.yml | Added separate PostgreSQL service/job and owner reset tests |
| 1736649f | services/api/app/models/auth_revocations.py | Persistent hashed JWT revocation data model |
| efdf59fa | services/api/app/security/token_revocation.py | Shared-DB revocation check and write helper |
| befa92fa | services/api/app/routers/auth_weweb.py | WeWeb logout/refresh persist revocation; missing table or DB unavailable blocks token use |
| d83cb59a | alembic/versions/20261119_persistent_auth_revocation.py | Additive, non-destructive WeWeb revocation schema after Factory migration |
| 0c7188a6 | tests/test_owner_reset_auth.py | Isolate legacy owner reset tests from revocation imports |
| 0b02fb6f | tests/test_weweb_revocation.py | Test persistence after new SQL session, duplicate revocation and missing schema |
| bc94cc4c | tests/test_auth_revocation_migration.py | Test schema upgrade, repeat and non-destructive downgrade |
| 2b1e4653 | .github/workflows/critical-controls-ci.yml | Add revocation, migration and auth regression tests |
| 9db6ee6a | .github/workflows/critical-controls-ci.yml | Added canonical full app import diagnostic on isolated runner |
| 2f766e94 | tests/test_postgres_migration_chain.py | Replay new Factory and auth migrations twice on disposable PostgreSQL |
| d6a35a28 | .github/workflows/critical-controls-ci.yml | Execute PostgreSQL migration-chain rehearsal |
| 5ce8e426 | services/api/requirements.txt | Normalize UTF-16 text into UTF-8 for reproducible Linux pip installs; pinned dependencies unchanged |
| 8a9788c5 | .github/workflows/critical-controls-ci.yml | Promote successful full app import and 9-route parity to mandatory gate |
| 10e635c1 | tests/test_db_fail_closed.py | Test deliberately invalid DB driver must stop startup |
| c12f2677 | .github/workflows/critical-controls-ci.yml | Add database startup negative test |
| 4187f97f | .github/workflows/critical-controls-ci.yml | Archive broad pytest collection errors as diagnostic artifact, not false all-green |
| dcbd0d18 | tests/test_db_fail_closed.py | Fix test subprocess CWD to canonical services/api package (not production code change) |
| eee4d389 | pytest.ini | Add canonical services/api import path to legacy test collection |
| 4f859eda | services/api/app/schemas/pack_sz_ta_tb.py | Disambiguate Python date annotation for Pydantic v2 |
| ae1f9850 | services/api/app/models/__init__.py | Expose canonical Base for legacy model imports |
| ddefbab5 | .github/workflows/critical-controls-ci.yml | Install missing respx in isolated test-only collection job |
| d0095b97 | services/api/tests/test_fake_live_operating_day.py | Remove unused reference to nonexistent OwnerCommand table; no replacement module fabricated |
| 1916ca53 | .github/workflows/critical-controls-ci.yml | Trigger tests on requirements, pytest config and historical backend test files |
| 58b897fc | ops/prime_system_integration_matrix.json | Update evidence levels for actual route import, PostgreSQL worker/migrations, and durable auth |
| 4aff8786 | ops/REMAINING_SYSTEM_BLOCKERS_2026-11-19.md | Publish evidence-based cross-source log review and blockers |

### CI truth

- https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44658342650: 85 targeted tests PASS (47 smoke, 35 isolated integration, 3 disposable PostgreSQL). Exact attempted test counts are from GitHub job logs.
- https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44657703945: canonical full FastAPI import passed; 7/7 required routers and 9/9 required routes present in a clean Linux runner.
- https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44659074502: source and system test gates passed. Backend pytest COLLECTION remains a separate non-gating diagnostic with 2 failures in historical modules.
- The last two collected import failures are services/api/tests/test_fake_live_operating_day.py (now requires an absent system_self_check router; rebuilding a safe authenticated real anomaly detector is separate work) and services/api/tests/test_system_integrity.py (expects old Deal/BuyerMatch interfaces not aligned with canonical ORM).
- Full backend tests have NOT been executed to completion. Passing 85 focused tests is not equivalent to all system features being DONE.

### Render and operational logs

- Initial broad Loki lookup failed with 503, but smaller date-scoped queries succeeded. Log retrieval failure ≠ app outage.
- Nov 19 daily cron execution logged HTTP 200 for /api/notify/daily-ops-email and completion; provider/inbox delivery not independently verified.
- No error-level API or cron events / API 5xx request logs returned in queried windows from Oct 25 through Nov 19 (no guarantee of full exhaustive log retention or no historic failures).
- API remains deployed from commit 93cb1afe8d7fbbc01385ea54d5fa992647be647b (Oct 10), not the PR development branch.
- GitHub checkout cleanup warns an archive submodule gitlink lacks .gitmodules entry; do not remove preserved archive without explicit review.
- Render: **NO service, env, cron, database, deployment, payment or schema mutation by these changes**.

### Immediate Dec integration focus

1. Reconcile the two legacy collection errors, then run the complete backend test suite.
2. Identify exact production API database and rehearse complete migration heads on a disposable production-like PostgreSQL copy.
3. Upgrade work queue from internal once-per-day draft proof to leased/recoverable business worker with real provider receipts.
4. Wire all external actions into the same owner-governed safety and idempotency boundary.
5. Implement true storefront/delivery/payment reconciliation, lawful marketing and independent opportunity discovery with actual proof.
6. Review whole PR and authorize staged deployment only after rollback and operator controls have been independently tested.


## PR review metadata reconciliation — November 19, 2026

- Updated draft PR #4 title/body to match observed scope: owner reset protection, fail-closed DB, persistent WeWeb revocation and migrations, real disposable PostgreSQL concurrency and migration rehearsal, actual canonical API import, 85 targeted passing tests, two remaining historical pytest collection errors, and narrow-window Render log findings.
- Current review: https://github.com/bryanevoy86-tech/Valhalla/pull/4 (draft; not merged). Recorded previous head 887db759761ece1f04331215c1355c3c8cd552b4. This ledger metadata update will create a newer head.
- CI sources: https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44658342650 (85 targeted tests); https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44659074502 (required app-import gate and focused jobs succeeded). Broad backend pytest collection remains diagnostic, with two failures; no full-suite certification.
- Render deployment/service/configuration/schema/environment mutations: ZERO. Existing live `main` commit unchanged; no database migration, provider action, paid service or real-world operation authorized or performed.


## Full Vision / AI Gods / Infinite Banking / Trust / Canada Exit scope recovery — 2026-11-19 (UTC CI Nov 20)

**Reason:** Owner correctly identified that the previous 25-domain integration audit foregrounded FastAPI/Business Factory at the expense of the agreed full enterprise vision. This round **does not claim to implement 21 missing systems**; it restores traceability, acceptance and safety boundaries in the same development branch.

| Commit | Scope | Evidence |
|---|---|---|
| b908389c | capital/banking/executor.py: fix false "executed" transfer with no bank call; now BLOCKS unconnected funds movement and does not consume authorization | Targeted CI |
| 1747db7a | tests/test_banking_transfer_fail_closed.py: five cases for no-provider, kill switch, destination whitelist, expiry and cap | Targeted CI |
| a33e330e | CI initial finance regression gate | Initial smoke failed because test requires pydantic |
| 5ceddbd6 | Move finance test to dependency-equipped CI integration job; all four CI jobs pass | Actions run 44661325096 |
| 47a5be65 | ops/VALHALLA_FULL_VISION_TRACEABILITY.md: explicitly index Pantheon variations, five legacies, sovereign Prime, Venture/Product Foundries, real estate, infinite banking, 90/10 funds, corporate/family trusts, Panama/Bahamas, Canada exit, tax residency, family payroll, Black Ice and resorts | Documentary traceability only |
| f529136b | ops/prime_system_integration_matrix.json: expanded 25→46 distinct source-anchored workstreams with acceptance/professional-gate requirements; no fake live verification | 46-path source preflight passed |
| 09abf7d2 | CODEX_START_HERE.md: mandatory full-vision scope before narrower passes | Documentation |
| 20217baa | docs/CODEX_SYSTEM_FINISH_PASSES.md: Pass 0 full scope, Pass 4 owner-private wealth/exit advisory and conflict resolution | Documentation |
| 95d1be73 | docs/HEIMDALL_DEFINITION_OF_DONE.md: include long-horizon wealth/Pantheon scope while distinguishing advisory completion from actual legal transactions | Documentation |
| 1419ba21 | docs/CODEX_RESUME_2026-12-01.md: December must include all 46 workstreams, never silently ratify conflicting doctrine | Documentation |

**Confirmed passing CI:** https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44662029960
- 47 smoke/static tests + 40 isolated integration tests including five new banking cases + 3 disposable PostgreSQL tests = **90 targeted tests passed**.
- Static source preflight reported **46 capability contracts**, no missing source anchors, and no asserted production verified domains.
- Canonical FastAPI critical router/9-route check passed on isolated Linux runner.
- Full enterprise integration and complete historical backend suite remain NOT verified.

**Material historical/doctrine contradictions flagged for owner decision:**
1. Original KING/QUEEN/ODIN/LOKI/TYR governance engine vs expanded Norse Pantheon/Bridge Layer and early Valkyrie/Fenrir/Skald/Jotunn labels. Do not duplicate roles or delete earlier intent.
2. Earlier Panama-first umbrella trust idea vs later Canadian-first/professionally reviewed future offshore doctrine; neither represented as an executed trust or automatically ratified decision.
3. Advisor-only Heimdall source docs vs intended bounded autonomous cross-industry Prime; owner, regulatory and financial authority must be explicit and enforceable.
4. Historical descriptions of "infinite banking" vs actual whole-life-policy data records. No insurer contract, cash-value loan or economic outcome proven.
5. Never equate a trustee/residency behavioral score model with actual legal trusts or tax residency.
6. The previously false-success internal banking executor is now blocked until a true provider receipt exists.

**External effects:** NONE. No insurer, bank, account, professional, tax authority or customer was contacted. No trust or residency change, payment, investment or payroll action performed. **Render mutation: ZERO**. Draft PR #4 is not merged or deployed.

The full owner-specific account, trust-beneficiary, tax residency, insurance and household details must be stored in a secure private vault later—not GitHub. The repository contains a requirements/architecture map, not a legal or financial file of actual documents.


## Original five-god Pantheon corrective integration — 2026-11-19 (UTC Nov 20)

Discovered during FULL VISION audit: 18/18 historical governance API tests initially returned HTTP 404 in https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44662500410. **Root cause:** original KING/QUEEN/ODIN/LOKI/TYR and governance_orchestrator routers use /governance prefix; tests and the orchestrator itself call /api/governance. Autoloading source files did not make the canonical endpoints actually available.

| Commit | File / action | Verification |
|---|---|---|
| 9023fe59 | CI adds actual historical original Pantheon tests as a diagnostic | Detected all 18 HTTP 404 |
| 9e0e5f08 | app/main.py: add backward-compatible /api/governance aliases for all five gods and orchestrator, preserving /governance paths | Real FastAPI tests passed |
| 61c0adca | core/route_integrity.py: require all 6 governance routers in critical readiness | CI passed |
| c4809bf0 | scripts/prime_runtime_route_probe.py: add all 6 canonical Pantheon HTTP route contracts (9→15) | Full FastAPI import CI passed |
| 426be5c4 | CI promotes 18 passing Pantheon tests and 15-route probe to required (NOT non-gating) | Run 44663174488 success |
| af64af6d | ops/prime_system_integration_matrix.json: original five Pantheon promoted to FOCUSED_CI_TESTED; expanded Norse roles remain source-only | 46 domain source preflight CI passed |
| 7dfd4120 | ops/VALHALLA_FULL_VISION_TRACEABILITY.md: record exact 404 root cause and new verified five-god proof | Documentation |
| b085405e | CODEX_START_HERE.md: update December owner command on tested gods vs unproven expanded pantheon | Documentation |
| 2ea302a6 | docs/CODEX_RESUME_2026-12-01.md: full fix/CI reference | Documentation |

**Verified CI:** https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44663174488
- 47 no-dependency smoke/static tests
- 40 SQLite/integration tests (includes five no-fake-bank-transfer tests)
- 3 real disposable PostgreSQL integration/migration tests
- 18 historical King/Queen/Odin/Loki/Tyr/governance-orchestrator FastAPI tests
- **108 targeted tests passed**. Canonical FastAPI app imported with **13/13 required router modules** and **15/15 required route paths**. Source matrix validates **46/46 source-anchored workstreams**, zero declared live verified.
- The complete historical backend suite still has two collection errors, notably missing system_self_check route and obsolete system_integrity models. No claim of full backend certification.
- The newly tested five original gods are **not** the entire Norse specialist bridge, do not enforce all provider actions and are not a production deployment.

**Render mutation / business external effects:** ZERO. No secrets, funds, insurance policies, trusts, residency filings, bank transfers or external provider operations were touched. Draft PR remains review-only.


## Loki as the independent second AI God — Nov 19/20, 2026

Owner clarified the original Loki doctrine: **an independent, equal-standing adversarial challenger of Heimdall**, detecting false assumptions, broken logic, wrong calculations, contractual contradictions, hidden tax/trust exposures, catastrophic downside, unsafe automations and strategy blind spots. Unlike Heimdall, Loki does NOT optimize business outcomes, create binding documents, self-approve, change trusts, move money, or execute provider actions. A controlled bridge shares versioned reports, preserving dissent and an owner-facing A/B/C/Override review. Re-run Loki after significant human/Heimdall changes.

Audit found:
- governance_loki.py: independently callable deterministic downside/ruin/correlation thresholds; included in 18 passing Pantheon API tests.
- ai/agents/loki.py: simple amount/risk-score based heuristic; NOT independent adversarial reasoning.
- core/loki_engine.py: explicitly a keyword/length-based synchronous stub.
- services/universal_opportunity_evaluator.py: useful in-process universal_loki_objections that can cause research-more/reject, but NOT an isolated independent second reviewer.
- routers/loki.py: create_loki_review previously generated a generic "stub" finding and labeled it COMPLETED; untrusted historical data could look audit-approved. Historical verdict path only used status/severity and could imply completed review without proof.

New development commits:
| Commit | Change | Result |
|---|---|---|
| 808486c5 | Stop the fake-completed Loki review code and return HTTP 503 until an independent audit worker exists | No false completion |
| c2851e68 | Forbid final Loki verdict from self-reported database flags/status even if an older row says COMPLETED | Fail-closed |
| 548270a6 | Seven tests: no provider, no existing review, unfinished, legacy stub, forged verified flag, critical universal objection, material objection | Targeted CI |
| 09b3688f | Include new tests in mandatory full-app governance regression job | CI |
| c24cc496 | docs/LOKI_INDEPENDENT_CHALLENGER_CONTRACT.md: owner doctrine, independent evidence/report requirements, high-risk triggers and acceptance tests | Scope restoration |
| bc9e745c | ops/prime_system_integration_matrix.json: adds Loki as first-class P0 independent workstream, **46→47** | Static preflight |
| 45148430, 64a0f0b5, c093e96b, 516cc57e, 182b3cfa | Main Codex handoff, definition of done, integration passes, December resume and full vision register updated to enforce Loki review requirements | Handoff |

**Actual green CI:** https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44678616870
- 47 static/smoke/policy, 40 SQLite/integration, 3 real disposable PostgreSQL, **25 Pantheon/Loki API and fail-closed tests** = **115 targeted tests passed**.
- 13/13 required router imports, 15/15 canonical route contracts, **47/47 source-backed workstream declarations** valid. NO independent Loki provider/workflow/live audit has been certified.
- Broad historical backend pytest collection still has two old import/contract errors. This is non-gating diagnostic; not a green full suite.

**Important remaining P0:** A genuine independently run and evidenced Loki audit worker, immutable proposal snapshots, adversarial source and counterfactual tests, re-audit after meaningful edits, unresolved-objection escalation, mandatory high-impact dispatch gate, and owner-visible side-by-side dissent. The implemented 503/409 defenses intentionally block the fake audit until that capability exists; do not conflate blocked mode with being operational.

**Render mutations:** ZERO. No production deployment, financial/legal operation, trust formation, customer contact, or provider transaction undertaken.


## 2026-11-20 — Owner-confirmed system-wide AI Gods and Prime authority clarification

Owner clarified that each God covers every relevant authorized subsystem and reports to Prime, who incorporates Loki's independent findings and makes and executes the best permitted operational decision. Updated existing documentation and acceptance matrix, retaining 47 workstreams. Routine authorized work is not per-action owner approval; mandatory high-risk gates and existing explicit authority limits remain. Exact role aliases still require historical reconciliation. Documentation-only; previous CI evidence pertains to prior tested code/matrix, no fresh runtime test claimed, no Render or provider actions.

- 4daa60e2 ops/VALHALLA_FULL_VISION_TRACEABILITY.md
- b7cdb4b8 docs/PHASE3_INTEGRATED_ARCHITECTURE.md
- 20597673 docs/LOKI_INDEPENDENT_CHALLENGER_CONTRACT.md
- 5553527e CODEX_START_HERE.md
- b3ea1cfb ops/prime_system_integration_matrix.json


## 2026-11-20 — Prime privacy, real decision integrity and standing routine authority

Scope: existing draft PR #4; 47 full-system workstreams and the owner-confirmed horizontal Gods doctrine preserved. No provider credentials, live operations or Render modifications. Commits:

| Change | Commit(s) |
|---|---|
| Separate Prime server control key, protect completion registry, Loki, decision outcomes, model-provider configuration; authenticated isolated registry fixtures | f313ebcf, 8fd0e136, 084bfbaa, 1523fdcb, e66f0a38, 6b3bd2c2 |
| Direct original five-God dispatch; full coverage and evaluation-only metadata, no external permission | 1bab8088, c9e7ab1c |
| Mimir per-engine/legacy/jurisdiction shadow feedback; no unverified current memory in historical/live evaluation; scoped test fixture | 1cd3499e, 7dd70f19 |
| Loki contradictory margin/capital objections; final lock after hard risk gates; Tyr/Forseti not verified | 0480ff3c |
| Eleven new Prime control and decision-integrity tests, require existing completion-registry tests in CI | 9093fa45, c6b2c014 |
| Actual bounded, expiring, revocable standing authority in existing internal draft worker; distinct owner authorization on grant/revoke and per-action approval; transactional consumption | da546749, 18b51b26 |
| Test credential separation, grant caps, revocation, expiry, scope, price limit, two-worker mandate cap | 04b91915, adf84f4d, 44a6114c, 89cf644d |
| 47-domain matrix and December continuation updated | f2b05ee6, 86769292, 456ed380 |

**Verified CI:** https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44748568129 all four jobs success on code commit 89cf644d. 47 smoke/static/policy + 45 isolated integration + 4 PostgreSQL + 94 selected pytest cases (including 58 completion-registry and 11 new Prime integrity cases) = 190 passing targeted tests. PostgreSQL proves one-use standing grant cannot be exceeded by two simultaneous workers; not provider/crash recovery proof. Earlier full app and selected test run 44748128884 and all-jobs standing-mandate run 44748399051 also succeeded. Broad legacy pytest collection remains non-gating with two import errors (fake-live operating day and system integrity); the full suite is NOT green. Latest documentation may be newer than tested code SHA.

**Deployment compatibility:** VALHALLA_PRIME_CONTROL_KEY / X-Prime-Control-Key required for four sensitive router groups. VALHALLA_OWNER_MANDATE_KEY / X-Owner-Mandate-Key must be distinct from the worker and Prime keys, and is required for new mandate grant/revoke and per-task approval in addition to the Factory key. No keys configured in Render this turn. Update trusted server-side callers, never store secrets in browser bundles or give them to model/worker prompts. New scope is INTERNAL_DRAFT_ONLY and no live grant exists. No new schema was added for mandates (uses existing legacy event and work tables). All other legacy API permissions still require examination.

**Remaining:** full 47 scope, especially independent actual Loki AI worker, system-wide scheduled and event-triggered God reports, real discovery/decision/verified execution and outcome learning, leased crash recovery, real provider integration, entire historical regression, live DB identification and full migration/rollback rehearsal, owner interface and professional-gated wealth/advisory tools. No claim of business or production completion.

**Render mutation count: zero.** No merge, deploy, DB change, cron activation, payment, bank transfer, account setup or customer contact. This is a branch-level implementation and test record.


## 2026-11-20 — Internal Factory receipt read-back integrity and local reconciliation handoff

Continuation remains on draft PR #4. Prior latest required CI run 44748568129 was inspected: all four jobs successful, with 190 targeted cases reported in the previous ledger. That does not certify these new changes or full historical backend tests.

| Change | Commit |
|---|---|
| Status read-back rejects wrong action/Legacy/event, malformed receipt fields, contradictory sales/external-effect flags and a digest-valid body not matching the expected listing | d8c73301b17ba53022271915a42cc1ab1b13afb5 |
| Two regression test methods, including seven malformed/misattributed receipt subcases and hash-valid substitution | e2443402182d1908e412727554fdfe4f19c8864b |
| Updated root Codex handoff: 47 workstreams, latest tested vs pending evidence, November 30 refresh target, local-only reconciliation and verified recovery gate | 826b760b424320a4d814bda0342ad5ab3dc5379f |

New receipt tests have **not yet been observed passing**. No fresh workflow result was returned for the test commit at inspection. The change is a bounded internal-record consistency check, not cryptographic proof against a malicious database writer, external publication, payment, or a complete worker lifecycle. Existing code still needs the full suite, provider receipts, verified learning, independent Loki, durable leases/recovery and the full 47-workstream integration.

Render read-only inventory confirmed API and daily-email cron on main with auto-deploy enabled, and both Postgres instances available. This does not identify the API's actual database or certify migrations. No Render mutations, production deploys, merges, external provider calls, payments, new paid services, or live mandates. Local VS Code work remains uninspected by the remote connector and must be backed up and reconciled before any integration. Never merge this draft to main before the existing staged release gates and specific authorization.


### Follow-up verification and Ice Wall continuity — November 20

CI run [44751720913](https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44751720913) on test commit e2443402 completed successfully in all four jobs. Factory integration job 136341001204 explicitly reports both new receipt tests as OK (16 pilot methods). This supersedes the pending-test statement above; no full-suite or production claim. Canonical app job 136341001722 still reports collection exit code 2: missing app.routers.system_self_check in test_fake_live_operating_day.py and incompatible app.models imports in test_system_integrity.py (first reported missing Deal). Do not satisfy these with fake compatibility aliases, stubbed success responses or skipped tests; reconcile the actual historical contracts against canonical models, routes and local-only changes.

Owner supplied the final Ice Wall architecture and scheduling handoff: continue the existing 47-workstream branch, implement horizontal proactive scheduled/event-driven Gods with independent Loki scrutiny, Prime decision and execution and scoped standing routine authority. Priority remains core stabilization, intelligence network with durable workers, real revenue operations, wider wealth/residency/protection ecosystem and controlled activation. Builder may run in parallel on isolated engineering assignments. The historical 150–340 engineering-hour range is an unmeasured estimate, not a guaranteed remaining-hours calculation. No changes to architecture, production, credentials or Render were made in this verification.


## November 20 — Ice Wall continuation: concurrent work, Builder isolation and internal polling

Actual commits (draft PR #4 only):
- d84c05de, 3dd9ae33, 98edf032: existing Factory transaction path handles concurrent idempotency races and scans past waiting/blocked work with individual row locks and rollback. Both queue regressions and both forced PostgreSQL submission races passed. CI 44754185070: all four jobs successful.
- e2b99d5f, b3bca920, 9c609809: existing Builder queue stores v2 snapshot/content-checksummed proposals, review verifies current base and exports exact bundle. Five real HTTP/ORM tests passed. CI 44754383354 all four jobs successful. Compatibility change: historical direct apply=true now refuses HTTP 409; old draft payloads must be regenerated and client release workflow updated. Do not confuse review_ready with test, merge or deployment.
- aa2e025c, bb56463b, 3070b468: independent Builder artifact materializer with new out-of-checkout artifact directory, scope, checksum, byte and syntax checks and non-execution receipt. Seven dependency-free tests passed. Configured default allowlist is deliberately bounded; expand only with explicit reviewed authority. Artifact does not establish code safety or functionality; actual isolated agent runner/test/PR integration remains.
- 78d41d28: two actual disposable PostgreSQL failure-injection tests passed for rollback after artifact flush and committed internal effect with lost worker acknowledgement. CI 44754821620 all four jobs successful. This is not OS-process kill proof or provider exactly-once execution.
- aedfa485, 54565c0e, 409b0a8c: opt-in standalone polling worker script; fresh DB sessions, schema checks, bounded polling/error backoff, emergency-stop delay, sanitized output. Four smoke methods and one real PostgreSQL tick integration passed in jobs 136352254096 and 136352253883 of run 44754991782. The full CI job conclusion was still being observed at the initial handoff. No worker started in production; no new Render service. Only internally authorized draft operations supported.
- d5ada453, 90ac7ebd: updated the original 47-workstream matrix and top-of-file Codex handoff. No workstreams deleted or marked production verified.

Reconciliation finding: the older remote codex/logout-contract-parity branch contains a substantial 1161-line system_self_check service and 393-line test file; corresponding canonical router and dependencies (including owner_command model) are absent from the working draft. Its completion registry/model changes overlap current security/learning work. Local-only changes remain unavailable. Both historical test-collection errors remain unresolved; do not invent stubs, skip tests or blindly merge the diverged histories. Preserve local state, verify encrypted restore, and reconcile the actual implementation. Keep all 47 domains, cross-cutting Pantheon, independent Loki, Mimir, private Prime, regional Legacy mirrors and repeatable clone playbooks distinct from safety copies, and wider financial/family/residency/protection scope.

No Render mutations, main pushes, merges, migrations, new paid services, production credentials, or external commercial effects. This is bounded branch-level implementation and evidence, not complete Valhalla or deployment certification.

**Final code-CI observation (Nov 20):** run 44754991782 completed all four jobs successfully, including the real PostgreSQL polling tick and the four standalone polling tests. The 23 newly added test methods across concurrency, queue fairness, Builder review, artifact materialization, transaction failure recovery and polling were observed passing in their designated CI jobs. Source matrix still contains 47 workstreams and zero production-verified entries. Read-only Render deploy lookup confirms the live API remains October 10 commit 93cb1afe. Latest documentation commits do not constitute a new deployed release. Full historical collection is not certified; the prior two mismatches remain. No production action performed.


## November 20 — Scheduled and standalone worker receipt parity

Continued existing draft PR #4, not main. Found scheduled HTTP tick accepted short arbitrary digest and missing sales/artifact fields; rejected legitimate blocked results. Standalone worker also accepted boolean/float zero and incomplete receipt identity, and used a scoped session registry rather than explicit fresh session factory.

- b0e4a2ce: require internal artifact type, positive integer media ID, exact action ID and SHA-256 format, integer zero external effects and explicit false sales flag; distinguish blocked/emergency stop from successful completion.
- d2c61264: tests for blocked states and twelve malformed/contradictory responses.
- 3d70fd77: align standalone receipt checks with HTTP tick and use SessionLocal.session_factory for fresh polling sessions.
- 4a9ea158: standalone receipt acceptance and rejection regression cases.

New tests committed; no new CI conclusion observed at this checkpoint. These checks establish receipt shape only, not independent remote/provider evidence. No scheduler activation or Render changes. Local clone attempt in chat environment failed DNS resolution, so full local test execution and reconciliation of local-only work remain blocked. The older self-check service explicitly imports absent OwnerCommand and other overlapping models; do not blindly copy or stub these. Existing 47 domain scope and two historical collection mismatches remain. Continue on this branch, not the separate documentation-only prep/december-2026-completion branch.


## November 20 — Credential separation and malformed header handling

Existing draft PR #4 only. Commit 0e99db78 rejects Prime control credentials equal to configured Builder, legacy session, JWT signing, Factory or owner mandate secrets; Builder and session comparisons now use UTF-8 bytes to avoid TypeError on non-ASCII credentials. c38df8e7 adds separation and malformed-input regression methods. a571c5f3 corrects Factory comparison; a6f3863c1 adds a direct authentication regression. CI run 44764148737 was in progress when inspected; do not assert new tests passed until job evidence is available. Existing worker receipt parity run 44762359005 confirmed all four jobs successful. No secrets changed, no production merge or Render mutation. New deployment compatibility gate: independently configure all control-plane credentials; do not copy into browser or model prompts. These changes do not certify complete tenant isolation or the independent Loki worker. Full local-state reconciliation and two historical collection errors remain open.
