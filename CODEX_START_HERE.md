# CODEX START HERE — Heimdall Prime integration (December 2026)

This is the one-file handoff from ChatGPT's November 19 development and audit. **Do not create new packs or restart Valhalla.**

## November 20 — Independent review and Mimir checkpoint

The historical suite passed all 280 checks in GitHub CI. The next implementation adds content-bound independent Loki review, mandatory reconsideration before non-shadow persistence, and one verified internal Factory outcome stream for Mimir. Review fixtures use independent test credentials and active local databases. A hosted reviewer, scheduled cross-system specialist coverage, provider-linked learning, and external release remain open. Start from the latest ledger entry and the 50-task register in the December handoff.

## November 20 — Historical regression closure

Full local backend execution passed all 280 historical tests. The required CI workflow now runs the complete suite. Contract, buyer, closer and HTTP regressions are resolved against isolated data and storage. See the latest ledger and the December handoff's reconstructed 50-task register. The next architecture gate is a content-bound independent Loki review with mandatory reconsideration before a non-shadow Prime decision is persisted.

## November 20 — Current engineering checkpoint

- Continue PR #4 on `fix/fail-closed-operations-20261119`. The latest entry in `ops/CHANGE_LEDGER.md` supersedes older claims below about the two historical collection errors. Full backend execution now runs and reports 218 passed, 60 failed and 2 skipped in isolated Linux. Canonical runtime probe verifies ORM configuration and 29 routes across 17 required router groups.
- Deal stage updates and audit writes now share one transaction. Private integrity GET reports observed controls and blocked learning work. Private POST records those alerts. Wider probes and automatic response remain open.
- The controlled operating-day and full intake regressions now pass. Intake writes lead, deal, explicit brief linkage and any underwriting freeze in one transaction. Both intake and status require the private Prime key. Reconcile the remaining closing, contract and alternate lifecycle routes with the same canonical data before merging. Compare the separate protected Windows checkout before integrating local-only work.
- The source preflight still covers all 47 workstreams. The exact numbered 50-task register remains to be reconciled with owner records. Follow the existing full-vision traceability and external-activation boundaries.

## ICE WALL CONTINUATION — latest engineering checkpoint, November 20

**Do not redo the fixes below.** They are committed on draft PR #4, not deployed.

- Factory internal queue: concurrent identical submissions reconcile; conflicting reuse is rejected; a blocked or waiting item no longer starves later approved work. Locks are released for unsuccessful candidates, with a fixed high-water mark per pass. CI 44754185070 passed all four jobs; two SQLite queue and two real PostgreSQL race methods passed.
- Builder: /builder/draft now stores a snapshot-bound v2 bundle, /builder/apply with approve=false prepares review, and GET /builder/tasks/{task_id}/review-bundle exports it. Five real HTTP/ORM tests passed in CI 44754383354. The old approve=true direct-runtime-write action now returns 409, intentionally; update callers. Regenerate old unversioned drafts. No generated code is executed or applied by the API.
- Builder artifact bridge: scripts/builder_materialize_review.py --review <export.json> --base-root <trusted-clean-code-snapshot> --output-parent <private-outside-checkout-dir>. Produces a new changed-file artifact directory and receipt; verifies base/content checksums and Python/JSON syntax without executing code. Seven tests passed in CI job 136351675452. Use an explicitly authorized, isolated runner for actual test execution and PR creation; no live credentials or source writes. This is not a complete autonomous Builder.
- PostgreSQL internal-action failure and lost-commit-ack tests passed in job 136351674897. No duplicate internal effects. This is not generic worker leases/process-kill or external-provider recovery.
- New optional standalone internal Factory polling script services/api/tools/cron/business_factory_worker.py requires explicit VALHALLA_INTERNAL_FACTORY_WORKER_ENABLED=1 and PostgreSQL configuration; it checks schema and polls fresh sessions with error backoff and emergency-stop delay. No Render configuration or activation. Latest new polling tests awaiting final CI observation at this checkpoint. Do not run against unknown DBs.
- Historical collection errors remain. The older remote codex/logout-contract-parity branch actually contains a substantial services/api/app/services/system_self_check.py and tests, plus later completion-registry work. It does NOT contain the required router or all owner-command/model dependencies. Local work may contain more. Reconcile this actual implementation rather than recreating it or skipping tests; compare against secured local checkout before merging either branch. See ledger. No whole historical suite claim.

Next: after independent encrypted local recovery/restore, reconcile the two development histories, resolve real missing self-check and obsolete integrity test contracts, finish whole-app test execution, integrate the existing Builder artifact handoff into a least-privilege coding/testing/PR worker, and connect system-wide proactive scheduled/event-driven Gods, independent Loki and Prime decisions to durable work and verified learning. Proceed in parallel with market discovery, Product/Venture Foundries, compliant marketing/customer acquisition, real order-to-cash and financial proof. Retain all 47 original workstreams, wealth/residency, household/secure founder chat and integrated provider responsibilities. No production merge, migration, external operation or new paid service without approved release and specific authority.

## CURRENT HANDOFF — November 20, 2026 (supersedes older counts and instructions below)

- Continue draft PR #4 on `fix/fail-closed-operations-20261119`; no merge to main. The last recorded successful required CI run is 44748568129 (190 targeted tests on code commit 89cf644d); all four jobs were independently checked green. The diagnostic historical collection still has two reported errors and is not a full-suite certification. See the append-only change ledger.
- New focused receipt-verification change d8c73301b17ba53022271915a42cc1ab1b13afb5 and regression cases e2443402182d1908e412727554fdfe4f19c8864b bind an internal listing's read-back status to its action, Legacy, receipt type and expected listing body. **New CI result not yet observed.** Review and run the required checks before treating this as verified.
- Latest owner-stated local Codex refresh target: November 30, 2026. Verify actual allowance before resuming. Older dates in the historical handoff are not deadlines.
- **Local checkout is a separate source of truth.** The November 15 local reports described a dirty `C:\dev\dev` checkout on `codex/logout-contract-parity`, with 225 passing offline workflow tests and a subsequent 262-entry work-state inventory. These are historical local claims, not current GitHub proof. The remote draft's 190 tests are a different suite; do not add the counts or assume one supersedes the other.
- Before switching branches, changing files, or attempting integration: confirm actual local root/branch/HEAD and working-tree state; obtain authorization for an independent encrypted recovery destination and verify restore; fetch without checkout; compare the local-only work (including the order-to-cash pipeline, founder approvals, WeWeb mappings and intake audit) against the remote draft. Use an isolated checkout/worktree only once recoverability is established. Do not reset, clean, stash, overwrite, force-push, blindly cherry-pick, or store local secrets/financial documents in the public repository.
- Preserve the entire 47-workstream vision. Priority is the secure commercial core plus Builder working in parallel, not creating new packs. Reconcile actual implementation collisions before developing missing dependencies. Do not infer live authority from internal draft grants.
- Next technical gates: full collection and regression without hiding the legacy mismatches; durable worker leases/restart/reconciliation; secure private Prime/owner interface and genuinely independent Loki; licensed market discovery and acquisition, actual delivery/collection and verified learning. Production API database identity, staged deployment and rollback remain unverified. No Render mutation or production activation in this continuation.

## DO NOT DROP THE REST OF VALHALLA

The master scope now has 47 source-anchored workstreams, not only the earlier 25 domains. **Read ops/VALHALLA_FULL_VISION_TRACEABILITY.md before any new code.** It covers the expanded AI Gods/Pantheon, original five-god governance, owner Commander A/B/C/Override, Norns, Mimir, five legacies, product and venture Foundries, 90/10 wealth/Fun Funds, whole-life policy infinite banking, trusts, Canada exit/residency, corporate finance, family succession, Black Ice, resort and expansion. Source-only does NOT equal completed. Do not silently resolve conflicting trust/Pantheon doctrine. No legal, tax, banking or insurer action without owner and relevant professional authority.

## Existing project

- Repo: https://github.com/bryanevoy86-tech/Valhalla
- Production: main, automatically deploys to Render.
- Continue work from branch: fix/fail-closed-operations-20261119
- Review draft: https://github.com/bryanevoy86-tech/Valhalla/pull/4
- Live production and Render have NOT been mutated by this branch.

## Read in this exact order

1. ops/VALHALLA_FULL_VISION_TRACEABILITY.md (full project vision and conflicting historical decisions).
2. ops/CHANGE_LEDGER.md (every development change, CI evidence, ZERO Render mutations).
3. ops/REMAINING_SYSTEM_BLOCKERS_2026-11-19.md (new cross-source log review and current blockers).
4. ops/prime_system_integration_matrix.json (47 source-anchored workstreams; acceptance conditions remain open).
5. docs/HEIMDALL_DEFINITION_OF_DONE.md (no more "finished" placeholders).
6. docs/CODEX_SYSTEM_FINISH_PASSES.md (the **three** ordered Codex work packages).
7. docs/CODEX_RESUME_2026-12-01.md (local Git commands, Render facts and current blockers).
8. docs/PHASE3_INTEGRATED_ARCHITECTURE.md (canonical Prime opportunity pipeline).

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


## Newly repaired and TESTED: original five-god Pantheon routes

Before: all 18 legacy King/Queen/Odin/Loki/Tyr/orchestrator tests returned 404 because the original router prefixes and API/war-table contracts disagreed. New branch mounts backward-compatible old /governance and canonical /api/governance paths, makes all 6 modules mandatory, and checks 15 exact API route contracts. 18/18 governance tests passed in isolated GitHub Actions run 44662885729. Pantheon tests have now been promoted to a REQUIRED CI gate. The broader AI Gods/Bridge Layer remains source-only until individually integrated and proven.


## Loki is a separate first-class God and mandatory challenger

Read docs/LOKI_INDEPENDENT_CHALLENGER_CONTRACT.md. Original governance Loki's threshold rules passing is NOT proof of the independent adversarial AI God. A legacy /loki/reviews endpoint previously forged COMPLETED from placeholder evidence; this branch blocks that until a verified independent reviewer exists, with regression tests. Codex must build independent scrutiny of Heimdall's immutable proposal, legal/financial/technical worst-case holes, source-backed dissent, re-audits after changes, and mandatory high-risk dispatch gating. Loki cannot edit Heimdall's originals, sign, move money, self-approve or bypass owner/professional authority. Owner receives both positions and chooses A/B/C/Override with all material objections recorded.

## Mandatory owner-confirmed clarification — 2026-11-20

Read the system-wide Pantheon doctrine at the end of ops/VALHALLA_FULL_VISION_TRACEABILITY.md before implementing the existing 47 workstreams. Every God must proactively cover every authorized subsystem matching its specialty, using event-driven and scheduled analysis, returning evidence and findings to Prime. Loki independently challenges whole-system proposals and relevant specialist findings. Prime makes the operational decision, incorporates material objections, executes and verifies within granted mandates. Do not turn Prime into an owner-prompt-dependent advisor or turn the Pantheon into a one-time review committee. Reserve owner approval for actions requiring it, authority exceptions and unresolved material issues; preserve legal/safety and existing production deployment limits. Prove cross-domain coverage and autonomous routine execution without per-action prompts. No new execution capability or authority is implied by this documentation update.

## November 20 integration update — read before changing code

The full 47-workstream inventory and owner-confirmed system-wide Pantheon doctrine remain authoritative. Additional code (not just design) is now on the branch:
- Separate VALHALLA_PRIME_CONTROL_KEY / X-Prime-Control-Key protects /api/completion, /loki, /heimdall/decisions, /system/models. Never expose this or any server secret to a subscriber, public WeWeb bundle, a model prompt, logs or GitHub. These routes will fail closed until secure configuration and server-side callers are updated. Complete all other Prime/subscriber isolation tests.
- The original five gods call directly in the existing governance orchestrator. Their response is advisory, including full_coverage, evaluation_only and external_effects_authorized=false. This is not the expanded scheduled/event-driven AI Gods network.
- Loki generic numeric inconsistency objections, final-recommendation snapshot after hard gates, and unverified Tyr/Forseti status replace misleading successes. Real separate Loki AI audit and dispatch integration still P0.
- Mimir shadow feedback is restricted by engine_id==domain, legacy==business_scope and jurisdiction. Live/replay decisions do not consume unverified current feedback, including claimed live-success records. Wire verified reconciled outcomes and as-of history with actual evidence; do not reintroduce contamination. Old JSON storage remains a separate unresolved path.
- The existing Business Factory worker now consumes finite standing mandate grants for INTERNAL_DRAFT_ONLY. Grant/revoke AND per-task approval need a distinct VALHALLA_OWNER_MANDATE_KEY / X-Owner-Mandate-Key in addition to existing Factory key. Do not give unattended agents the owner key. Worker requires only X-Business-Factory-Key. Grant includes mandate_id, exact legacy/business/engine/jurisdiction/product scope, ttl_seconds (60–604800), max_uses (1–100), max_price_cents_cad. POST /api/business-factory/mandates, POST /api/business-factory/mandates/{mandate_id}/revoke; submit listing-drafts with mandate_id. Grant row lock, use event and draft receipt share the SQL transaction. Owner action-specific approval remains supported.
- No mandate is granted in production. This is ONLY an internal local draft capability. No posting, spend, legal action, customer data, payment, transfer or code deployment authority.
- Required CI expanded to execute the existing full test_completion_registry.py plus Prime privacy/decision-integrity tests. Run 44748399051 succeeded. PG job 136330161525 in run 44748568129 passed a two-worker, one-use mandate test. Full historical pytest collection still reports two old errors, not full suite green.

Before deployment: reconcile local checkout and review latest PR/CI; configure separate server-side keys securely only after authorized migration/release; update trusted callers including internal tooling, cron and frontend server; test all auth and policy routes, revoke/expire/concurrency, verify database target, backups and rollback. No direct main push, provider credentials or production activation. Continue full specialist bridge, independent Loki, true discovery, leased recoverable worker, provider settlement/publishing and the whole 47-workstream vision. Do not downgrade regulated/wealth planning scope.
