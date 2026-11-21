# Codex / VS Code — Valhalla Resume Handoff

Planned resumption: when local Codex usage allowance refreshes, expected December 1, 2026.

DO NOT restart the project, regenerate completed packs, or treat API presence as operating business evidence.

## Repository and change control

- GitHub: https://github.com/bryanevoy86-tech/Valhalla
- Stable Render production branch: main (auto-deploy on push).
- Working development branch: fix/fail-closed-operations-20261119
- Draft PR: https://github.com/bryanevoy86-tech/Valhalla/pull/4
- Persistent changelog: ops/CHANGE_LEDGER.md
- Definition of done: docs/HEIMDALL_DEFINITION_OF_DONE.md
- Existing architecture: docs/PHASE3_INTEGRATED_ARCHITECTURE.md and docs/UNIVERSAL_OPPORTUNITY_PIPELINE.md

## Reconstructed 50-task register

This working register maps three cross-workstream integration tasks and all 47 owner workstreams to the existing acceptance matrix. The numbers are reconstructed from available requirements. Each workstream retains its existing source anchors, dependencies, and acceptance criteria. Code presence and local tests do not confer external authority.

| Task | Deliverable or workstream ID | Priority |
|---|---|---|
| 01 | Resolve the historical backend regression suite without exclusions or fabricated outcomes | P0 |
| 02 | Reconcile local-only Windows changes with verified recovery and a reviewed integration diff | P0 |
| 03 | Exercise a controlled end-to-end rehearsal spanning evidence, specialist dissent, owner authority, a bounded worker action and durable learning | P0 |
| 04 | `api_wiring` | P0 |
| 05 | `auth` | P0 |
| 06 | `runtime_governance` | P0 |
| 07 | `discovery_sources` | P1 |
| 08 | `universal_evaluator` | P1 |
| 09 | `knowledge` | P1 |
| 10 | `learning_mimir` | P1 |
| 11 | `legacy_instances` | P0 |
| 12 | `legacy_execution` | P0 |
| 13 | `schema_and_migrations` | P0 |
| 14 | `scheduling` | P0 |
| 15 | `builder_code` | P0 |
| 16 | `ai_providers` | P1 |
| 17 | `marketing` | P0 |
| 18 | `media` | P1 |
| 19 | `subscription_saas` | P1 |
| 20 | `commerce` | P0 |
| 21 | `finance_webhooks` | P0 |
| 22 | `payouts_and_funds` | P0 |
| 23 | `contracts_legal` | P1 |
| 24 | `real_estate_execution` | P1 |
| 25 | `notifications` | P1 |
| 26 | `operations_observability` | P0 |
| 27 | `weweb_frontend` | P1 |
| 28 | `ci_release` | P0 |
| 29 | `prime_private_owner` | P0 |
| 30 | `pantheon_five_evaluators` | P0 |
| 31 | `pantheon_expanded_bridge` | P0 |
| 32 | `norns_probability_calibration` | P1 |
| 33 | `owner_commander_voice` | P1 |
| 34 | `five_initial_legacies` | P0 |
| 35 | `clones_vs_mirrors` | P1 |
| 36 | `product_foundry_subscriptions` | P1 |
| 37 | `independent_venture_foundry` | P1 |
| 38 | `real_estate_portfolio_legs` | P1 |
| 39 | `treasury_banking_controls` | P0 |
| 40 | `infinite_banking_insurance` | P1 |
| 41 | `estate_and_master_trusts` | P1 |
| 42 | `canada_exit_strategy` | P1 |
| 43 | `global_residency_options` | P1 |
| 44 | `tax_opinions_legal` | P0 |
| 45 | `reinvestment_funfund_policy` | P1 |
| 46 | `family_payroll_succession` | P2 |
| 47 | `bahamas_resort_growth` | P2 |
| 48 | `shield_blackice_protection` | P1 |
| 49 | `recruitment_and_va` | P2 |
| 50 | `loki_independent_challenger` | P0 |

### Safely retrieve current work

From your existing local folder C:\dev\valhalla:

    git status --short
    git fetch origin
    git switch -c codex-business-factory origin/fix/fail-closed-operations-20261119

If there are uncommitted local changes, preserve them before switching. Do NOT reset or delete local work. If the branch name exists already, choose a new name. Codex must compare local-only work against GitHub before merging any changes.

## Code already on the development branch

- Scheduler, reference outbox dispatcher, daily ops and cron runner corrected to stop reporting nonexistent successes.
- Heimdall readiness changed to conservative evidence-based checks.
- New Business Factory worker in services/api/app/services/prime_business_execution.py.
- New authenticated endpoints in services/api/app/routers/prime_business_factory.py.
- Existing DB records reused: LegacyInstanceWorkItem, LegacyOrchestrationEvent, LegacyInstanceRegistryItem and MediaContent.
- Five false-success smoke tests plus five SQLAlchemy/FastAPI integrated Business Factory lifecycle tests.
- CI workflow: .github/workflows/critical-controls-ci.yml.
- Initial false-success CI: https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44630305972
- Business Factory integration CI: https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44635299115

New pilot is INTERNAL_DRAFT_ONLY: persistent, idempotent, owner-approved, verified record and receipt. No claim of a storefront, payments, generated downloads, marketing or sale. All new pilot API calls require X-Business-Factory-Key, compared to the secure server-side VALHALLA_FACTORY_KEY. Missing key = HTTP 503. The required key has NOT been set on Render in this work.

## Required Codex next actions (in order)

1. Read the ledger, acceptance contract, this handoff and PR #4 before writing code.
2. Fetch the branch. Run focused and integrated CI tests in an isolated environment. Review tests for meaningful proof and inspect legacy full-suite errors without hiding or ignoring them.
3. Inspect the current factory service and route for full import/auto-registration, database concurrency safety, idempotency collision protection, governance, safe auth, policy sync, status reporting, receipt integrity, and actual behavior.
4. Verify which Postgres database production API uses, without exposing credentials or changing schemas. Current Render inspection showed one empty public schema and one with 367 tables.
5. Implement and prove a durable worker scheduler with safe retries and restart behavior on actual Postgres, using the existing work registry. Do not use in-memory state for business-critical jobs.
6. Build the minimum actual Product Foundry loop in this same execution system: validate asset bytes/hash/version and license; owner-approved storefront listing; payment-provider verified sale; delivered download; refund/reconciliation; accurate daily profit summary.
7. Connect actual authorized marketing, campaign attribution, and conversion reporting. No false "published" status, spamming, or paid advertising without approval.
8. Feed actual outcomes to Mimir and reuse existing cross-industry opportunity scoring. Then add source-driven independent discovery that produces the same governed work records.
9. Re-run complete tests. Maintain an evidence table per capability: code, focused test, real integrated test, staging proof, deployed commit, live receipt and outcome.
10. Propose a controlled deployment and rollback plan for owner approval. Do not push to main or change Render service configuration without that approval.

## Current Render inspection — 2026-11-19

- Workspace: tea-d3fbf3r3fgac73b3ed40
- API service srv-d3hatinfte5s73cqbbh0: live Git commit 93cb1afe (October 10).
- Daily email cron crn-d5u469npm1nc73d9n350: recent successful runs, not a business task executor.
- Postgres dpg-d90l1mv7f7vs73cod580-a: public tables = 0.
- Postgres dpg-d9ek3oj7uimc73fooes0-a: public tables = 367.
- No Render production changes have been made by this effort.
- Production API database identity remains unverified.
- Do not print or commit credentials. Do not create new paid Render services casually.

## Paste this prompt into Codex on resumption

Continue the CURRENT Valhalla / Heimdall Prime codebase. Start with a safe git fetch, review GitHub PR #4 (branch fix/fail-closed-operations-20261119), and read ops/CHANGE_LEDGER.md, docs/CODEX_RESUME_2026-12-01.md, docs/HEIMDALL_DEFINITION_OF_DONE.md and docs/PHASE3_INTEGRATED_ARCHITECTURE.md. Preserve all existing local-only changes. DO NOT create more standalone packs, reset the repository, or mark simulated functionality complete. Verify the real FastAPI and SQLAlchemy integration of the new owner-approved Business Factory execution lane and its SHA-256 receipts. Run all new CI checks, diagnose broad-suite failures, and then build the missing durable Postgres worker/recovery, actual product artifact storage, provider-backed storefront fulfilment, verified sales/refunds/accounting, lawful automated marketing, and proactive multi-industry opportunity discovery into ONE canonical governed end-to-end lifecycle. Reuse the existing Prime, legacy, Phase Three evaluator and Mimir modules wherever possible. Record every file/commit, CI link, Render action and real-world evidence in ops/CHANGE_LEDGER.md. Do not push to main or deploy production until I authorize a reviewed release; do not expose secrets or spend funds. The final deliverable must demonstrate a real business from independent discovery through verified execution, customer delivery, and reconciled profit, not endpoints that only return success.

## Handoff success criteria

- Local Codex reads exact committed GitHub changes, not reconstructed chat prompts.
- Tests pass in a clean checkout, with known failures recorded.
- Every operation returning completed has an independently verifiable receipt.
- Any remaining setup requiring the owner's external accounts or legal/financial approvals is explicitly identified.
- No production impact until a reviewed release is authorized.


## Added after initial handoff: scheduled execution and database preparation (Nov 19)

- Existing Render daily cron command is services/api/tools/cron/daily_email_ping.py. It now optionally calls business_factory_tick.py AFTER successful email; no second paid cron service is created.
- The optional tick is DISABLED by default. It requires BOTH BUSINESS_FACTORY_RUN_URL and VALHALLA_FACTORY_KEY. The URL must be HTTPS, an exact path, and an explicitly allowed host. It rejects redirects, missing credentials and unverifiable success.
- No keys or URLs were configured on live Render. This is SOURCE-CODE PREPARATION, not a deployed worker.
- The populated Render Postgres db-v2-copy was inspected read-only. It has media_contents and alembic_version, but is missing legacy_instance_registry_items, legacy_instance_work_items and legacy_orchestration_events.
- Its current alembic_version was 8e43f380be7f on Nov 19. The repository has an existing subsequent revision 20261007_shadow_source_governance.
- Migration alembic/versions/20261119_factory_legacy_work_schema.py now prepares missing factory tables after the existing governance revision. It preserves existing tables and will not drop business data on downgrade. Review and apply only on an approved deployment.
- API router requires all four persistent tables before running. It returns HTTP 503 with missing-table details rather than reporting false success.
- More tests: tests/test_business_factory_cron.py and tests/test_factory_migration.py. The GitHub workflow exercises dry-run email/worker-cron security and idempotent non-destructive migration against disposable SQLite.
- Root alembic is at alembic/ (not services/api/alembic/). Dockerfile starts services/api/start.py. Render web service currently has an empty pre-deploy command. Do not assume migrations happen automatically.
- Before any production deployment: establish which database the API actually uses, run an isolated migration rehearsal, validate new auth, review live business data and rollback posture, then obtain owner approval.

**Current live Render services and database have NOT been mutated.** Updating GitHub's isolated development branch does not change Render production until main changes or a deployment is explicitly triggered.


## December system-wide preparation extension (2026-11-19 evening)

This handoff now has a root entrypoint and THREE ordered integration prompts:

- CODEX_START_HERE.md — one prompt that starts from existing local work.
- docs/CODEX_SYSTEM_FINISH_PASSES.md — Pass 1 engine/security, Pass 2 Product Foundry, Pass 3 general autonomous Venture Factory.
- ops/prime_system_integration_matrix.json — 25 source-anchored capability acceptance contracts.
- scripts/prime_system_preflight.py — read-only, token-free source integrity scanner.

Latest expanded targeted CI: https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44652624533
49 targeted tests passed; 25-domain source preflight good. This is NOT a green full-suite or live production certification.

Additional code changes on the SAME development branch:
- services/api/app/core/builder_path_policy.py and routers/builder.py: file traversal and symlink prevention, repo root resolution, digest verification, block direct Git pushes.
- services/api/app/providers/stripe_adapter.py and webhooks/stripe.py: correct Stripe signed timestamp HMAC; no unprocessed payment acknowledgment.
- services/api/app/integrations/stripe/payouts.py: real transfers are blocked until provider implementation, no fake IDs.
- services/api/app/services/media_engine.py and marketing_service.py: no unsupported published states.
- services/api/app/routers/marketing.py: older marketing CRUD mounted under owner key.
- services/api/app/routers/media_engine.py: owner key required.
- services/api/app/core/route_integrity.py and main.py: critical router failures surfaced; /readyz blocks missing critical routes and defaults to DB/heartbeat checks.
- services/api/app/core/dependencies.py: no default anonymous session-token access; explicit development-only environment switch.
- New targeted tests cover each of these safety requirements.

Important compatibility warning: the stricter authentication, router readiness and external publication-state transitions are deliberate behavior changes and must undergo full integration regression before merge; do not deploy solely on the 49 focused test successes.

No Render configuration/service/database/deploy changes have occurred. Auth keys, bank accounts and external provider credentials require owner authorization. The new branch does not prove external autonomous business execution.

When Codex resumes, read CODEX_START_HERE.md first and take PASS 1 to green before PASS 2/3. Reconcile any local VS Code-only changes before switching branches.


## Latest canonical API route probe and 53 passing targeted tests

- New script: scripts/prime_runtime_route_probe.py.
- Exact route contracts checked: owner identity, Phase Three legacy registry, Business Factory submit/run, marketing, media, SaaS plans, Builder and readiness.
- Its four unit tests pass, but **the actual canonical FastAPI application has NOT yet been imported and verified** by this scripted probe.
- Run in isolated Python environment after all dependencies/test DB configured:

    python scripts/prime_runtime_route_probe.py --import-app --json

- Do not run this with production external API keys. Imports can execute application initialization, so inspect that environment.
- Latest 53-test CI: https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44653459058 (targeted only).
- Do not mistake source preflight or route registration for functioning live business operations.


## Autonomous AI risk safeguards (November 19 addition)

Source and acceptance: docs/PRIME_AUTONOMY_SAFETY_CONTRACT.md.
Implementation: services/api/app/core/autonomy_governor.py, connected only to the internal approved Business Factory draft in services/api/app/services/prime_business_execution.py. Stop inputs: VALHALLA_EMERGENCY_STOP environment variable and the go_live_state database kill_switch_engaged when that table exists. Shadow external actions always blocked; high-impact calls require review; no actual provider actions wired.

Targeted regression suite: 71 passed at https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44654950056

Critical caveat: This is NOT production global enforcement. For the current internal-no-external-effect pilot only, absence of historical go_live_state table is tolerated by the governor. Real money/outreach/deployment adapters must require durable active policy and fail closed if state missing. Owner approval must be obtained from authentic, persisted and scope-locked records, never an AI-generated field.


## Current audit state and verification (Nov 19 / UTC Nov 20)

Start at root CODEX_START_HERE.md and then ops/REMAINING_SYSTEM_BLOCKERS_2026-11-19.md.

- 85 targeted tests passed: https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44658342650.
- Real canonical app import and 9 API routes registered in GitHub CI: https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44657703945. The full app import is now a required CI gate.
- Disposable PostgreSQL verified two workers never both completed the same approved internal product draft. Factory and WeWeb auth migrations reran idempotently and preserved a pre-existing record; no live Postgres mutation.
- Owner password recovery now requires configured matching setup secret. app.core.db cannot silently start ephemeral in-memory SQLite on invalid driver/schema.
- WeWeb logout/refresh now store SHA-256 hashes of revoked JWT IDs in shared SQL table auth_revoked_access_tokens; additive migration at alembic/versions/20261119_persistent_auth_revocation.py. The login/logout flow must be staged/tested against the full app after migration.
- Backend pytest collection diagnostic still has two historical model/route mismatches; see triage. Full backend suite NOT green.
- services/api/requirements.txt was converted from UTF-16 to UTF-8, pinned dependencies unchanged.
- Render filtered API/cron logs returned no error-level/5xx matches in queried windows and Nov 19 daily email completed; no claim of successful business automation.
- No changes were made to production Render services/configuration/DB. The code requires owner-approved staged release with migrations first.


## Full Valhalla scope restored — November 19

Do not limit December to 25 broad technical contracts or the Product Foundry. The expanded machine matrix now contains 47 source-anchored workstreams, including full Pantheon/Bridge Layer, Norns/Mimir, voice Commander, five legacies, banking, 90/10 funds, whole-life infinite banking, trusts, Panama/Bahamas planning, Canadian exit/residency, legal/tax opinions, family payroll, Black Ice and more. Master register: ops/VALHALLA_FULL_VISION_TRACEABILITY.md. Pass 0 reconciling all requirements is obligatory before the three technical integration passes, and Pass 4 privately scoped professional-gated wealth/exit advisory implementation comes after the safe operating engine.

Critical additional safety fix: capital/banking/executor.py formerly returned executed with no real bank transfer. It now fails with BANK_TRANSFER_PROVIDER_NOT_CONNECTED and leaves owner approval unused; tests/test_banking_transfer_fail_closed.py added. No bank account was accessed or funds moved.

Conflicting doctrine (Pantheon names, Panama-first vs Canadian-first, advisor-only vs owner-approved autonomous execution) is flagged for owner decision. Do not silently force either side.


## Original Pantheon integration newly repaired

A real audit found that all 18 historical five-god tests were initially 404. The original routes used /governance; the orchestrator and tests expected /api/governance. The branch now supports both paths, checks all 6 original Pantheon routers as mandatory and tests 15 canonical endpoint contracts. The 18 real FastAPI governance tests passed after the fix (Actions 44662885729) and are now a mandatory CI requirement. The expanded Model C Norse specialists are NOT thereby deployed or connected to every external provider dispatch.


## Loki independent challenger priority fix

Loki must NOT be categorized only as original five-god governance or simple risk threshold evaluator. Inspect services/api/app/routers/loki.py, app/ai/agents/loki.py, core/loki_engine.py, services/universal_opportunity_evaluator.py and docs/LOKI_INDEPENDENT_CHALLENGER_CONTRACT.md. A false-completed review stub was blocked to prevent bogus audits; tests/test_loki_audit_fail_closed.py proves missing engine and self-issued evidence don't pass. The real independent AI audit worker, durable provenance and dispute-loop remains a P0 implementation task, no production proof.

## November 20 continuation checkpoint

- Task 01 is closed at b4ff3188. All 280 historical backend tests run in required CI with zero failures and zero skips. [Verified CI](https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44801703651)
- Tasks 08, 10 and 50 advanced at 7afbd9cd. Prime's live recommendation persistence checks the exact independent Loki receipt. Material findings require a durable owner response and critical findings block advancement. Mimir verifies Factory receipt and artifact bytes in scope before returning an internal outcome. The independent analyst process and provider-backed outcome ingestion remain open. [Verified CI](https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44802792727)
- Tasks 14 and 31 now have an opt-in scheduled advisory lane for owner-approved registered legacy, business, engine and jurisdiction scopes. See `services/api/tools/cron/specialist_schedule_worker.py` and `/api/prime/specialist-schedules`. Cadence, expiration, cancellation, policy changes, emergency stop and report receipts are exercised. No worker was started against a deployed environment. Next extend this same lifecycle to event-driven discovery and independent God workers, merge their scoped observations into Prime proposals, then require independent Loki review and the applicable work-item mandate.
- Task 03 still needs an integrated rehearsal through actual independent review and an authorized work-item action. Reuse the Factory verified-draft and Mimir receipt path. For commercial execution, continue from a real, licensed artifact through provider test settlement, verified delivery, refund and reconciliation before owner-authorized activation. Preserve separate product and independent venture paths, the initial Legacies, mirror/clone distinctions, and the regulated wealth-workstream acceptance evidence.
- Task 15 now includes `scripts/builder_test_review.py`. Use an independently prepared local Docker image with the backend test dependencies, pass its image ID and the exact committed base SHA, and supply the exported Builder review JSON. The runner uses the committed test suite and reports the process exit with the bundle hash. Builder tasks cannot invoke Docker from the API. Continue wiring durable assignment, scoped review evidence and approved PR creation separately.
- Task 36 now has durable internal Product Foundry staging. `POST /api/business-factory/product-artifacts` stores verified product bytes, an exact scoped version and an owner internal-use rights reference. With `artifact_id`, the existing Factory lane binds a draft and its Mimir outcome to that version and revalidates it before execution. Corruption or revocation blocks a pending action. This is the handoff point for a future rights-cleared test storefront, authenticated checkout, fulfilment and settlement reconciliation.
- Task 03 has an integrated internal rehearsal in `services/api/tests/test_product_artifact_workflow.py`. A scoped asset and exact listing proposal passed through the independent Loki receipt interface and mandatory owner reconsideration. The eligible Prime snapshot then authorized assignment to the existing internal lane, where a one-use owner mandate authorized execution. The worker bound and revalidated the asset and the exact reviewed proposal, and Mimir retained both digests. The test emulates an independent reviewer with a distinct credential; the real analyst process, licensed discovery sources, external fulfilment and payment reconciliation still need integration.

- Task 35 advanced by securing the legacy clone and mirror policy APIs and correcting dispatch claims. Metric evaluation remains available to Prime. Unsupported dispatch leaves cooldown state unchanged and writes a deny audit record. Continue with distinct business clone playbooks and regional mirror provisioning; verify durable work plus actual isolated runtime evidence before either reports an active result.
