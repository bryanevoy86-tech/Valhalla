# Codex / VS Code — Valhalla Resume Handoff

Planned resumption: when local Codex usage allowance refreshes, expected December 1, 2026.

DO NOT restart the project, regenerate completed packs, or treat API presence as operating business evidence.

## Start here — current continuation

Use the current head of draft PR #4 and confirm the latest required CI run. Use the current workstream index, integration matrix and latest ledger verification to choose unfinished work. Dated checkpoints and original prompts are historical records. The same index supersedes earlier execution orders in the root start page and the finish passes. There are 50 acceptance contracts, 53 task entries and seven construction packages.

## Current workstream index and startup order

For tasks 04–53, follow the workstream ID in the task register to the corresponding row in `ops/prime_system_integration_matrix.json`. Each row provides exact `source_paths`, `depends_on`, implementation state and an evidence level. Read the `continuation` fields for existing test evidence, next implementation and the owner action, then use the unchanged `acceptance_test` as the proof contract. `production_verified` remains false where real operation has not been established.

| Task | Current evidence and source | Remaining work and dependency | Owner action and acceptance evidence |
|---|---|---|---|
| Cross-cutting 01 | Full backend regression passes. Canonical gate is `.github/workflows/critical-controls-ci.yml`. | Keep the full suite green through additive migrations and a reviewed staging release. | Existing internal verification authority. Preserve the complete test result and any genuine exclusions. |
| Cross-cutting 02 | The current draft is the verified shared continuation point. Local Windows differences remain unverified in this runtime. | Obtain an actual Windows diff if changes still exist. Review commits and resolve scope conflicts before any merge. | Provide the local diff or checkout only if it contains changes that must be recovered. Acceptance is a reviewed file/commit comparison. |
| Cross-cutting 03 | `services/api/tests/test_economic_control.py` and `services/api/tests/test_product_artifact_workflow.py` exercise scoped research, owner decisions, internal execution, and fixture settlement. | Connect one separately authorized staged provider and extend worker interruption and proof over an end-to-end run. | Authorize the named staging providers and test scope separately. Acceptance requires independent receipts and scoped Mimir outcome lineage. |

Startup sequence is private owner interaction, authorized source ingestion, economic feasibility, reviewed internal execution, then approved staging proof. Historical wealth engines remain optional candidates. Regulated banking, tax, professional, insurance, trust and expansion activity retains its dedicated approval gates.

## Repository and change control

- GitHub: https://github.com/bryanevoy86-tech/Valhalla
- Stable Render production branch: main (auto-deploy on push).
- Working development branch: fix/fail-closed-operations-20261119
- Draft PR: https://github.com/bryanevoy86-tech/Valhalla/pull/4
- Persistent changelog: ops/CHANGE_LEDGER.md
- Definition of done: docs/HEIMDALL_DEFINITION_OF_DONE.md
- Existing architecture: docs/PHASE3_INTEGRATED_ARCHITECTURE.md and docs/UNIVERSAL_OPPORTUNITY_PIPELINE.md

## Reconstructed task register and later workstreams

This working register maps three cross-workstream integration tasks and all 47 owner workstreams to the existing acceptance matrix. The numbers are reconstructed from available requirements. Each workstream retains its existing source anchors, dependencies, and acceptance criteria. Code presence and local tests do not confer external authority. The original entries 01–50 remain intact. Entries 51–53 map to acceptance workstreams 48–50.

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
| 51 | `investment_and_trading_intelligence` (workstream 48, Package 7) | P1 |
| 52 | `currency_arbitrage_and_fx_intelligence` (workstream 49, Package 7) | P1 |
| 53 | `dynamic_capital_allocation_loss_containment_and_strategic_redeployment` (workstream 50) | P0 |

### Safely retrieve current work

On Windows, open PowerShell in the actual VS Code project folder and verify it on resumption. The November paths were historical and this Linux run cannot inspect them.

```powershell
$repoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) { throw 'Open the actual Valhalla checkout and retry.' }
$remoteUrl = git -C $repoRoot config --get remote.origin.url
if ($remoteUrl -notmatch '^(https://github\.com/|git@github\.com:)bryanevoy86-tech/Valhalla(\.git)?/?$') {
    throw 'Verify the checkout origin against draft PR #4 without printing credentials.'
}
git -C $repoRoot status --short --branch
git -C $repoRoot fetch origin fix/fail-closed-operations-20261119
if ($LASTEXITCODE -ne 0) { throw 'Resolve the fetch before switching branches.' }
git -C $repoRoot log -1 --oneline FETCH_HEAD
git -C $repoRoot log --left-right --oneline HEAD...FETCH_HEAD
```

Compare the fetched SHA to the draft PR. Preserve local-only commits and pending changes for review. Use a separate worktree from `FETCH_HEAD` if the active checkout has changes, and record the verified absolute path on resumption.

## Historical checkpoints

Each dated section below preserves implementation history. Use the current index above for execution order.

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

## Original execution sequence (archived)

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

## Historical Render inspection — 2026-11-19

- Workspace: tea-d3fbf3r3fgac73b3ed40
- API service srv-d3hatinfte5s73cqbbh0: live Git commit 93cb1afe (October 10).
- Daily email cron crn-d5u469npm1nc73d9n350: recent successful runs, not a business task executor.
- Postgres dpg-d90l1mv7f7vs73cod580-a: public tables = 0.
- Postgres dpg-d9ek3oj7uimc73fooes0-a: public tables = 367.
- No Render production changes have been made by this effort.
- Production API database identity remains unverified.
- Do not print or commit credentials. Do not create new paid Render services casually.

## Original resumption prompt (archived)

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
- Tasks 10, 14 and 31 now have one event-driven path from verified work to fresh specialist advice. Use `on_verified_outcome` on an authorized schedule. Factory writes its Mimir evidence and follow-up request together. The worker revalidates evidence before evaluation and leaves cadence intact when triggered early. External discovery and independently operating specialist workers remain open.
- Task 35 now includes `POST /api/prime/legacy-playbooks` for an owner-authorized business clone or regional mirror registry rehearsal. `GET /api/prime/legacy-playbooks/{target_id}` returns its exact source policy version, target namespace and type-specific remaining evidence. The target remains inactive. Continue with signed policy propagation, independent runtime/isolation evidence and actual staged replication or fresh business rollout before reporting live readiness.

## Package 1 private inference checkpoint

Owner advisory requests default to PRIVATE. Only an explicit SYNTHETIC turn can use the opt-in external lane. It additionally requires release approval, a configured daily request limit, provider-specific approval, DB emergency state and environment emergency stop clearance. Previous turns, documents and system evidence stay local. Review authorized staging configuration separately. These constraints supersede earlier instructions that allowed replay of prior chat text. Mirrors are regional operating instances of a Legacy, and clones reproduce proven business playbooks.

Private Jarvis conversations now accept explicit source-turn-backed memory records via the thread's /memory API. Scope defaults to the conversation, and OWNER visibility makes an entry available across the private owner workspace. Corrections supersede an existing record and retain provenance. “What do you remember?” and “Open obligations” retrieve local records. A turn may explicitly reference a persisted specialist schedule receipt, which is shown as advisory evidence. These APIs confer no execution approval. Route all requests through an authenticated owner server proxy and supply stable client UUIDs for replay.

The private attachment extraction endpoint is POST /api/jarvis/conversations/{conversation_id}/attachments/{attachment_id}/extract. Reuse its hash-bound receipt with “Review attached extraction” and the same attachment ID. Output remains local and untrusted. Next work includes scanned PDF OCR, image interpretation under an approved data policy, file retention/revocation and the authenticated WeWeb owner proxy.

Norns now records owner-estimated odds before an internal Factory action and resolves against a verified receipt and deadline. Use /api/prime/norns/forecasts and /api/prime/norns/calibration. This produces measured internal samples. Continue with model-specific forecast definitions, independent outcome adapters, temporal holdouts, regret and commercial calibration separately.

Provider suitability is available at /api/prime/provider-intelligence. It compares owner-supplied synthetic boundary outputs for exact active registered models. The advisory recommendation cannot dispatch a call. Loki excludes the Prime default identity. Continue with dated provider catalog evidence, measured costs and latency, private-local policy, controlled role-specific benchmarks and an independently operated Loki model. In Jarvis, a turn may reference either specialist_schedule_id or prime_decision_id to retrieve internal recommendations with durable source links. The complete internal rehearsal is in services/api/tests/test_product_artifact_workflow.py.

### WeWeb owner conversation contract

Use a same-origin authenticated owner server proxy. The proxy holds the Prime key and authenticates the owner on every request. Preserve client-generated thread, turn, attachment and memory UUIDs when retrying. Owner chat remains private by default. Content returned in turns, memory, or extracts is data and should be rendered as escaped text.

| UI action | Private upstream contract |
|---|---|
| Resume from phone or computer | GET /api/jarvis/conversations and GET the selected thread's /turns |
| Retrieve a cited local knowledge brief | POST a turn with knowledge_domain and, for regional evidence, knowledge_jurisdiction |
| View specialist or reviewed Prime evidence | POST a turn with one specialist_schedule_id or prime_decision_id |
| Record or correct a preference, obligation or decision | POST to the thread's /memory with source_turn_id and, for corrections, supersedes_id |
| Read uploaded evidence | Upload to the thread, call the attachment /extract endpoint, then send a “Review attached extraction” turn with the attachment ID |

Model requests do not carry this data. The authenticated proxy and voice interface still need implementation and acceptance. For staging, start with these local contracts and run the real provider smoke only after explicit authorization. Retain evidence of transport identity, privacy and budget limits before release.

## Active intelligence continuation

Enroll explicit scopes at POST /api/prime/pantheon/assignments. A process using services/api/tools/cron/pantheon_worker.py takes owned role assignments on their cadence or verified Factory outcome. Each role is mapped to a local monitoring lens. Extend those adapters to the full authorized subsystem map and licensed research sources. Review a specialist receipt using its /challenge endpoint. When a proposed Prime decision includes specialist_inputs.pantheon_report_ids, both the decision and the referenced current report require independent review and reconsideration. Factory checks them again at execution.

The local Loki worker runs from services/api/tools/cron/loki_analyst_worker.py using only the separately scoped reviewer credential and HTTPS queue origin. It performs independent local checks and has no provider or release authority. Staged role transport is available at /api/prime/provider-intelligence/stage-probes for fixed synthetic benchmark cases only. Leave it disabled until authorized staging verification. Owner briefings now show current internal evidence and unreconciled amounts; reconcile actual account and provider settlement before claiming cash or revenue verified.

Builder can now queue a prepared review candidate at /builder/assignments with its exact Git base and pinned image. scripts/builder_assignment_worker.py uses a distinct runner credential and the existing network-disabled sandbox to return test evidence. Candidate generation and reviewed GitHub changes remain separate tasks. Attachments now support local image OCR when Tesseract with English language data is installed. Scanned PDF rendering, upload disposition and retention controls remain open.

Norns role assignments can issue one historical-rate estimate when matching observed history is sufficient. Forecasts retain training lineage. Compare worker estimates with the separate SCOPED_HISTORICAL_RATE calibration cohort. The attachment /review endpoint records owner dispositions against the exact source hash; a rejected file stays in the private inbox and is blocked from extraction and conversational use. Next independent work includes real source-driven discovery, role-specific analysis across all subsystem adapters, independent model-backed Loki staging, actual provider cost reconciliation, candidate generation and the dependent household and wealth workflows.

## Package 1 continuation and Package 2 internal rehearsal

Read the corresponding change-ledger entry and the updated integration matrix before changing code. The reviewed code checkpoint through signed campaign attribution is `de5a9ef5ce3205cac29e83cedb7286dd06efeedf`. Its [four GitHub gates passed](https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44858299580). Continue from the current draft PR branch head, which also includes bounded Builder candidate preparation and the handoff.

| Area | Existing integration and next unfinished work |
|---|---|
| Specialist analysis and Foundry | Register private, date-bound research at `POST /api/prime/foundry/evidence`, then let the already enrolled scoped Gods run. Review the candidate citing the specialist and exact evidence before Prime and Factory. Extend beyond the six Foundry lenses to remaining authorized subsystem adapters and independently sourced discovery. |
| Loki and providers | Dated owner-attested prices, role benchmarks, synthetic usage reconciliation and eligibility ranking live under `/api/prime/provider-intelligence`. Model recommendation confers zero dispatch authority. Obtain explicit staging authorization, then verify independent Loki credentials and distinct model, privacy rules, real transport and actual metering before any further release. |
| Norns | Use `POST /api/prime/norns/forecasts/{forecast_id}/holdout` before deadline or resolution. Check ordinary and independent holdout cohorts by estimate source. Next add governed forecast targets beyond the verified internal artifact, with independently observable outcomes. |
| WeWeb and attachments | A revocable owner JWT can read `GET /api/weweb/owner-briefing`. The API does not send the Prime key to the browser. Existing private inbox extraction now attempts bounded local OCR for scanned PDF pages when Poppler and Tesseract are available. Finish the conversation proxy, retention, image analysis beyond extraction, voice and proactive notification delivery. |
| Builder | `POST /builder/assignments/prepare` takes a bounded, owner-authorized single literal replacement against an exact source hash, Git base and pinned runner image. It queues the existing isolated test worker and records the candidate without writing the worktree. Autonomous selection and authoring of broader work, plus reviewed GitHub submission, remain open. |
| Package 2 | Keep local checkout, attribution and refund fixtures separate from the commercial ledger. Continue independent acquisition underwriting, real-estate operations, actual SaaS engine tenant isolation, licensed checkout and settlement, paid entitlement renewal, and consent-bound attribution. Live commercial verification requires separate authorization. |
| Package 3 | The private floor view now separates unreconciled amounts by month and currency. Continue household obligations, verified treasury reconciliation and internal reinvestment/Fun Funds modelling. Infinite banking, trusts and Canada exit remain separate planning workstreams. |

## Package 7 continuation — Investment, trading and FX

- Keep research and execution separate. The market API has no brokerage, bank or provider executor. The old /arbitrage order and metrics paths are owner-protected paper bookkeeping. Audit historical vault values with independent statements before relying on them.
- Under `/api/prime/market`, register exact-scope batches via `POST /evidence`. The Source Registry must allow practice and the owner must attest internal rights. Operator-reported evidence needs a registered live-class source. This designation does not certify the underlying report. `GET /evidence/{id}/research` reads the instrument, macro or quote evidence. Revoke a stale or erroneous record by ID.
- `POST /replays/investment` supports whole-unit buy-and-hold and previous-close moving-average signals at the next supplied open using split-free, aligned daily bars. The declared costs apply to both portfolio and benchmark. It returns marked values and per-observation statistics. No annualized risk or actual fill claim is made.
- `POST /replays/fx` compares direct conversions and models sequential two-leg or three-leg loops, including failure and a bounded partial fill. Results are per-currency paper postings and include residual exposure. The controls assume successive quote validity after each prior settlement and no leverage. Provider transfer charges and prefunded parallel fills are outside this replay.
- Norns market forecasts use `/api/prime/norns/market`. A forecast pins one future UTC date, a threshold and a different registered outcome source. Competing closes block resolution. Calibration excludes revoked evidence and reports separate holdout and evidence-class metrics.
- The floor's `POST /api/governance/floor/wealth/scenarios` models household budget and expenditure, operating reserves, planned owner compensation, and the 90/10 split of remaining scenario cash. It neither adds revenue nor transfers funds. Treat the reserve-and-compensation ordering and supplied cap as explicit scenario assumptions.
- Next work includes authorized source connectors with independently dated reference data, currency and securities lifecycle cases, explicit FX outcome calibration, reconciled market and bank records, independent model-backed Loki staging, and advice review with licensed professionals where applicable. Continue the Foundry, property, commercial tenant, Builder, attachment, voice, trust, insurance and residency work recorded above.
- Package 7's source and replay implementation is `8deacf179d33df5a5beb0ddc8ed44615045455c7`. The paper-vault correction is `c063ada8b1102618a42f29fd16314099cc74f64f`. Acquisition downside modelling is `04edcb978abdd94d83245a41b47ec6ebc70cff0f`. Its optional Foundry inputs cover acquisition cost, financed principal, transition cost, reserves, and debt service. The scoped Njord worker identifies stress-case cash shortfalls and does not approve financing.

## Universal economic control and strategic redeployment

Code checkpoint `ba302311e6d5c17c46e61bc2df662ffa5a34cb04`. Read the change ledger and `engines/ENGINE_REGISTRY.md`. Under `/api/prime/economy`, enroll scoped mandates, then enter dated performance and per-currency liquidity fixtures and registered opportunities. Amendments must bind the previous mandate. Opening history and cumulative loss persist, reserves remain protected and the budget counter serializes competing allocation rehearsals. Review an exact `/review-artifact` through the existing Loki API and independent worker with `--artifact-type economic_advice`, then record the reviewed outcome at `/decisions`. The independent worker uses the existing separate reviewer authority.

Use `/containment` to protect an enrolled Factory lane immediately. No endpoint allocates actual funds or automatically resumes a contained operation. Future integration needs independent bank and obligations reconciliation, reviewed winding-down and recovery case lifecycle, scoped cash release rules, full portfolio coverage, and internal priority tradeoffs with each Legacy. Preserve advisor-only investment authority and continue the private WeWeb, voice, notifications, Builder, SaaS, real estate, and regulated planning workstream backlog.

## Startup operating integration checkpoint

1. Register approved practice sources typed `DEMAND_EXPORT` or `PROCUREMENT_EXPORT` and scoped specialist assignments. Submit owner-authorized exports at `POST /api/prime/foundry/intake`. The opt-in `foundry_discovery_worker.py` uses the existing PostgreSQL worker controls and the explicit `VALHALLA_FOUNDRY_DISCOVERY_WORKER_ENABLED` flag. Inspect durable jobs by ID. Recheck source rights and freshness when generating a candidate from the scoped report. Losing source authorization invalidates that candidate.
2. Use the existing economic registry for ranking. A reviewed `RESTART` binds the exact current assessment and cannot increase exposure. Late, disputed, or open tracked obligations can block restart. Cancel an unneeded simulated reservation via `/reservation-releases`. Lifetime funded totals and losses stay in force. `/portfolio-exposure` returns per-currency aggregates and missing evidence counts.
3. Use private floor statement fixtures to reconcile period continuity and bank-like transaction references. Keep household and operating reserve accounts separate. The legacy vault audit projects suspect paper FX amounts separately. Exit recovery fixtures require a classified statement entry and preserve projected versus observed fixture amounts. Existing wealth scenarios remain the path for reserve, compensation and Fun Fund projections.
4. Rehearse signed Product Foundry checkout, delivery and refunds, then attach `/orders/{id}/cost-fixtures`. Contribution covers the recorded fixture costs. Real profit remains unknown.
5. WeWeb owner JWTs read `/api/weweb/owner-conversations` and scoped turn history. The existing owner briefing shows durable discovery state and errors. The browser receives no Prime key.

Startup-critical next work includes independently authorized market-source connectors, enrollment and controls for the actual startup paths, complete purchase-to-settlement rehearsals with real receipt formats, independent bank reconciliation, full authenticated WeWeb interaction and retention, 24/7 staging soak, and audit-ready professional preparation. Keep live inference, spending, external commerce, banking, trading and deployment separately authorized. Continue the wider owner vision in its existing workstreams.

## Owner and startup evidence continuation — November 21, 2026

- `POST /api/weweb/owner-conversations` and thread suffixes `/turns`, `/attachments` and `/attachments/{id}/extract` use the private owner bearer and existing JARVIS store. Browser turns are forced to local processing. `/owner-briefing?mode=driving` provides short read-only output for eventual voice rendering.
- Attachment dispositions still require the separate owner mandate. `retain_until` is an inclusive UTC date. Once elapsed, ordinary download, re-extraction and saved-extract disclosure are blocked. At this checkpoint only read suppression was available. The disposition follow-up below supersedes that limitation for active storage.
- Mimir's decision record accepts purpose, rationale and scoped memory dependency IDs. “Review past decisions” lists differences under an exact normalized topic without making a finding about truth or authority.
- `PUT /api/prime/foundry/intake/sources/{source_id}/signing-key` enrolls a publisher public key with an owner mandate. External export intake is still a signed-file handoff. No outbound source execution is configured.
- Product Foundry fixture settlement compares signed event deltas with unique indexed statement entries. Existing refunds remain available during emergency containment. This rehearsal produces no actual settlement receipt.
- Builder claims expire and only three lease attempts are available before `lease_exhausted`. The owner briefing shows remaining recorded failures. Restart the approved staged worker under the existing configuration only after the independent staging authorization.

## Current continuation evidence

- Owner disposition is implemented in `services/api/app/services/owner_conversation.py` and `alembic/versions/20261123_owner_disposition.py`. `DELETE /api/jarvis/conversations/{conversation_id}/attachments/{attachment_id}` requires the private Prime key and the separate owner mandate. The body binds `source_sha256` and `reason` (`OWNER_REQUEST` or `RETENTION_EXPIRED`). The route removes active bytes and extraction copies in one transaction and retains a tombstone. Expiry still blocks access after the inclusive UTC date. Batch deletion and backup retention/restore verification remain open. Existing authored chat and review history stay available.
- `GET /api/weweb/owner-conversations/{conversation_id}/attachments` uses the revocable owner bearer, returns metadata with `Cache-Control: no-store`, and shows tombstones. Browser disposition requires the existing separate owner approval path. Test references are `services/api/tests/test_owner_conversation.py` and `services/api/tests/test_saas_tenant_entitlements.py`.
- `services/api/app/pantheon/monitor.py` consumes duplicate triggers using digest-verified reports and accounts for missed cadence slots without moving the next deadline on replay. The work-queue lens reports overdue recorded work within exact scope. The private briefing and driving view project sampled missed cadence evidence. `services/api/tests/test_pantheon_assignments.py` checks replay, tamper rejection, recovery and scope separation. Multi-worker staging soak, domain-specific coverage, and event backlog handling remain open.
- Next internal review starts with the matrix rows for `pantheon_expanded_bridge`, `scheduling`, `weweb_frontend`, `notifications`, `owner_commander_voice`, `discovery_sources`, `product_foundry_subscriptions` and `treasury_banking_controls`. Continue through other authorized unfinished rows as their dependencies allow. The [ledger](../ops/CHANGE_LEDGER.md) records the exact development commit and verification.

## External verification readiness

The following are staging gates for existing workstreams. Record the approved environment, connector, scope, budget and expected evidence before each test. Staging hosts, account identifiers and costs that have never been approved remain pending. Keep credential values server-side and out of receipts.

| Integration and endpoint | Credential and test scope | Cost and side effects | Expected receipt and owner authorization |
|---|---|---|---|
| Render API/worker and PostgreSQL. Staging service IDs/host pending; `GET /health` and mandatory route probe against the selected application. | Existing staging project/service access and staging-only database URL. Test disposable migration, restore, forced worker interruption and restart with synthetic rows. | Hosting quote pending. Possible staging build, process restart and schema writes; no production DB access. | Service and build IDs, commit, Alembic head, isolated DB identity marker, checksums and a timed recovery log. Owner approves the staging resources, access, cost and window. |
| WeWeb private preview. `POST /api/weweb/login`, `GET /api/weweb/owner-briefing`, and `/api/weweb/owner-conversations` as documented above. | Project editor access and a synthetic staging owner/subscriber pair with revocable JWTs. Verify session continuity, tenant denial, cache headers, disposition receipt display and logout on two clients. | Existing plan and preview cost unconfirmed; preview edits, session and fixture storage only. | Preview revision, redacted request/response evidence and revocation receipt. Owner approves the exact preview project and writer access. |
| Owner Groq adapter. `POST https://api.groq.com/openai/v1/chat/completions`. Alternate OpenAI owner endpoint in `owner_advisory_model.py`; separately approved only. | Server-side `VALHALLA_OWNER_CHAT_GROQ_KEY`, explicit owner-chat release and model allowlist, synthetic data class and request cap. Staging-only smoke test of one approved request and outage handling. | Free-plan evidence and request quota required before any call. One synthetic payload and token usage; paid fallback disabled. | Provider request/model identity, recorded status and reconciled tokens with provider receipt. Owner separately approves the exact synthetic payload class, model, limits and inference. |
| Independent Loki. `POST /loki/worker/reviews/{review_id}/result` and `POST /loki/reviews/{review_id}/reconsider`. External model vendor/URL pending. | Separate reviewer identity and `VALHALLA_LOKI_REVIEWER_KEY`, plus a distinct staged model credential when selected. Exercise an exact fixture digest, material objection, rejection and reconsideration. | Model costs or zero-cost allowance unverified; staged review writes and approved synthetic inference only. | Independent reviewer/model attribution, source/result digests, objection and reconsideration receipts. Owner approves the independent model, separation, synthetic inputs and budget. |
| Source discovery. `PUT /api/prime/foundry/intake/sources/{source_id}/signing-key` and `POST /api/prime/foundry/intake`. Upstream host and export rights pending source selection. | Publisher Ed25519 public key plus owner mandate, a licensed signed export and exact Legacy scope. Test duplicate, stale and wrong-scope records. | No API fee for local fixtures. Any outbound connector price, pull scope and data terms require approval; staging jobs and reports persist. | Source license, timestamp, export digest, intake receipt and scoped finding. Owner approves the source, terms and permitted access. |
| Checkout and settlement. Fixture `POST /api/prime/foundry/rehearsal/payment-fixtures` and `/orders/{order_id}/settlement-fixtures`. Merchant test account and callback destination pending. | Selected provider’s test-only key and webhook signing secret server-side. Exercise authorized test checkout, fulfillment, duplicate refund and statement reconciliation. | Sandbox cost and any webhook email effects require confirmation. Synthetic order and fulfillment only. | Signed provider event IDs, order/delivery identity and matched statement entry. Owner approves merchant, callback, products and synthetic scope. |
| Bank statements and QuickBooks. `/api/prime/economy` statement fixture contract and `services/api/app/integrations/quickbooks/client.py`; bank endpoint and company realm pending. | Approved read-only sandbox bank credential or signed sample statement. QuickBooks sandbox OAuth app/realm with scoped test access. Compare opening/closing balances, fees, unmatched entries and duplicate imports. | Vendor fees unconfirmed. Staging imports or synthetic sandbox entries only; no transfers. | Statement provenance, reconciliation report and remote journal/readback IDs when configured. Owner approves institution, realm, data access and any write. |
| DocuSign and Google workspace. Legacy adapter paths `services/api/app/integrations/docusign/client.py` and project storage integration; demonstration account, exact instance and folder pending. | DocuSign demo integration credentials, scoped consent and synthetic envelope; Google test workspace OAuth or scoped service account and private fixture folder. | Vendor/license costs unconfirmed. Test only controlled envelope recipients and disposable documents, with explicit consent for email or remote writes. | Provider-generated envelope/file IDs, signature or access receipts and cleanup record. Owner approves destination, access scope and test side effects. |
| Notifications and voice. Existing private briefing `GET /api/weweb/owner-briefing?mode=driving` and fail-closed `outbox_dispatcher.py`. Provider and send/speech URLs pending. | Approved sandbox sender and controlled test recipient or device-local speech permission. Check consent, deduplication, outage and emergency controls. | SMS, voice or email costs unknown; funded or recipient-facing tests require separate approval. No sensitive briefing content in fixtures. | Transport acceptance and provider delivery/readback, or a device-local voice replay trace. Owner approves opt-in destinations, channel, payload and cost. |
| Marketing, real estate, acquisitions, SaaS pilot and professional preparation. Existing Foundry/Legacy scope interfaces; external project, recipient, portal and exact endpoint pending provider or professional selection. | A scoped pilot/test account for any external connector. Professional document exchange uses separately approved access and reviewed redacted material; no blanket mandate. | Quotes and contact scope pending. Any outreach, filing, agreement, activation, signing or regulated step requires specific authorization. | Provider receipt or dated licensed reviewer sign-off with scope and disposition. Owner selects recipients and authorizes each external action. |
| Investment and FX market data. Existing advisory replay interfaces. Named licensed data/broker feed and sandbox endpoint pending. | Read-only test data credential scoped to timestamped quotes and provenance. Exercise replay, costs, stale quotes and classification. | Data-license fees unconfirmed. Quote readback only. | Source timestamp, venue/license and replay receipt. Owner approves source access and fees. Trading and transfers remain outside scope. |
