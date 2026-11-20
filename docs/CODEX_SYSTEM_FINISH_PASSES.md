# Heimdall Prime — Three Codex Integration Passes
Last prepared: 2026-11-19
Development branch: fix/fail-closed-operations-20261119
Review PR: https://github.com/bryanevoy86-tech/Valhalla/pull/4

This is an ordered execution plan, not three promises of instant completion. Run a pass until its acceptance gate is green. If a real provider, account authorization, design choice or funding is required, stop at OWNER_ACTION_REQUIRED, record evidence and do not fake a result.

## Original scope that MUST NOT be lost

- Heimdall Prime is a private owner-only multi-industry autonomous business operator.
- Product Foundry commercializes selected isolated subordinate systems as subscriptions, never Prime itself.
- Venture Foundry independently discovers, designs, launches and operates distinct lawful businesses, not just a single contractor toolkit.
- Existing real estate, contracts, finance, lead acquisition, grants, arbitrage, media, marketing, SaaS, residency, governance, security, learning and five-legacy work must be reused and integrated where technically real.
- No uncontrolled expenditure, customer outreach, legal/regulated commitment, code deployment, owner data transfer or live payment without policy authorization.
- Success means durable execution with independent receipts and observed outcomes, not status text or a development-pack number.

## Preparation sources

Read in order:
1. ops/CHANGE_LEDGER.md
2. ops/prime_system_integration_matrix.json (25 P0/P1 domain contracts)
3. docs/HEIMDALL_DEFINITION_OF_DONE.md
4. docs/CODEX_RESUME_2026-12-01.md
5. docs/PHASE3_INTEGRATED_ARCHITECTURE.md
6. GitHub PR #4, all changed file diffs and review/CI results
7. Current Render API, cron and Postgres service identity (read-only first)

Safe VS Code commands from existing checkout:

    git status --short
    git fetch origin
    git switch -c codex-prime-finish origin/fix/fail-closed-operations-20261119

Preserve any uncommitted or unpushed local work before switching. Do not reset, force push, delete files or merge until user review.

### PASS 1 — ENGINE, SECURITY & RELEASE FOUNDATION

COPY TO CODEX:

> Work inside the EXISTING Valhalla repository, continuing the GitHub working branch linked to draft PR #4. Read the persistent change ledger, the 25-domain matrix, the strict definition of DONE and the current integration handoff. Do not add more packs or rebuild existing components. Your first task is to certify the canonical API and infrastructure: import the full FastAPI app, fix any mandatory router omissions or failures, unify root app/app.routes/app.routers paths, verify WeWeb JWT/RBAC and persisted token revocation, fix all silent auth bypasses, and test owner/multi-tenant boundaries. Reconcile the true Render Postgres connection without printing credentials, rehearse the prepared Alembic migrations on disposable PostgreSQL, prove Schema HEAD, and write/execute owner-approved durable work items with row leasing/idempotency, retry/backoff, dead-letter handling, revocation, timeout and restart recovery. Replace process-local business state with durable storage only where needed. Keep code generation isolated to a reviewed branch/PR and disallow any direct main push. Run the complete repo test suite; fix actual failures and classify environmental defects explicitly. CI must fail if a critical module doesn't import, a task can claim an unperformed outcome, or a production provider adapter fakes success. Add exact tests and receipts, record each file/test/commit/Render action in ops/CHANGE_LEDGER.md. Never change production without an explicit reviewed release approval. End by presenting the completed tests, actual runtime evidence, unverified conditions and an exact P0 next-action list.

Before considering PASS 1 complete, run the read-only route probe from an **isolated test environment** with test credentials and the full backend dependencies:

    python scripts/prime_runtime_route_probe.py --import-app --json

This command has not yet been run successfully against the canonical app. Record missing imports/routes and fix them instead of accepting a healthy /health response. The new source scanner is `python scripts/prime_system_preflight.py --json`.

PASS 1 must show:
- Canonical API import and documented OpenAPI endpoint contract parity pass in a clean environment.
- Every required critical router either loads or fails readiness; no hidden capability loss.
- Authentication and owner isolation enforce correct barriers; no anonymous writes.
- Code Builder cannot traverse/write elsewhere or push directly to main.
- Disposable PostgreSQL migration and concurrent work/duplication/restart tests pass.
- Render identity, DB revision and deployment source logged (no secret output).
- An authenticated user can initiate APPROVED work and obtain a checksum-verified stored output after worker execution.
- No production DB or deployment mutation without explicit consent.

### PASS 2 — REAL PRODUCT FOUNDRY AND COMMERCIAL PROOF

COPY TO CODEX AFTER PASS 1:

> Continue the accepted canonical work queue and security layer. Implement the first COMPLETE Product Foundry operating loop without developing a parallel standalone architecture. Use Valhalla Digital Products as the initial pilot but keep the whole subsystem multi-product and multi-tenant: verified product asset bytes/version/license and safe storage, approved storefront listing, Payhip or other owner-authorized checkout/delivery provider, verified signed paid-order/refund webhooks, durable deduplication, real payment/fee/refund settlement reconciliation, ledger and tax-friendly reporting, and customer entitlement controls. Connect marketing using approved channels and provider-specific publish/readback confirmations; an internal social post is NOT published. Measure attribution and conversions back to authenticated paid orders. Connect subordinate SaaS subscription provisioning and cancellation without exposing Heimdall Prime or tenant data. Ensure no paid AI tokens or ads are used unless the owner explicitly sets an approved budget. Create a provider sandbox acceptance harness that injects duplicate events, delayed transfers, outages, refunds, cancellations, retries and malicious signature attempts. All successful status responses must be supported by independent receipts. Stop when outside provider registration or owner account authorization is needed and mark OWNER_ACTION_REQUIRED. Never generate fictional purchases or claim revenue from tests. Keep all production writes blocked until approved and validated.

PASS 2 must show:
- Exact asset and approved listing record; no invented storefront listing URL.
- Provider-signed order events consumed exactly once; any refund reverses accounted revenue correctly.
- Buyer download/delivery evidence and proper entitlement isolation.
- Recorded marketing publication has a real provider receipt or remains unverified.
- Price, fees, costs, tax fields and net real income are separate from forecasts and shadow data.
- No outside account setup or production charge initiated without the owner's authorization.

### PASS 3 — GENERAL AUTONOMOUS VENTURE FACTORY & END-TO-END PRIME

COPY TO CODEX AFTER PASS 2:

> Integrate all existing Phase Three universal opportunity evaluation, source/rights governance, independent research ingestion, Mimir outcome learning, five-legacy coordination, and the Product Foundry into ONE Heimdall Prime business lifecycle. Prime should independently schedule lawful, budget-limited research for multiple industries, record provenance and recency, rank opportunities using the existing specialist/Norns/Loki/Pantheon/exit analysis, abstain when evidence is weak, issue governed owner-approval requests, then assign only authorized activities to actual durable workers. Execute through provider adapters that prove real outcomes, isolate per business/jurisdiction, monitor costs/revenue/risks, automatically follow up where permitted, learn from actual outcomes while preserving immutable shadow/holdout boundaries, and safely propose iterations or new ventures. Join real-estate deals, subscriptions, finance, research, media, marketing, contracts and customer operations to the same event/receipt spine; avoid parallel duplicate abstractions. Test five separate business legacies concurrently, worker death, repeat triggers, credential expiry, provider outage, legal/professional block, mismatched tenants, and unsuccessful opportunities. Build an owner console (WeWeb) that shows EXACT statuses, blocked owner approvals, proof receipts and audited money flows. Test the whole flow in sandbox and staged provider environments before proposing any real-world activation. Keep Prime private; market only explicitly approved subordinate products. Record every version and proof in the ledger. Nothing is DONE because a blueprint, test fixture, HTTP 200, mock or forecast exists.

PASS 3 must show:
- Source-triggered discovery -> scored/abstained evaluation -> owner decision -> durable authorized work -> proof -> measured outcome -> Mimir learning -> next schedule.
- Concurrency tests for five legacies show strict namespace, jurisdiction and authority separation.
- Business Factory can independently propose a new opportunity instead of only accepting human input.
- Proven costs/fees/revenue are reconciled; no unsupported projections shown as earnings.
- Owner approval, safety stop, kill switch and recovery/failover are exercised in an integrated harness.
- All connected user interfaces reflect actual backend status rather than optimistic flags.
- Actual external production side effects require explicit release and policy authority.

## Final release / live-proof boundary

A final production release needs reviewed code, clean CI, migration rehearsal, backup plan, verified owner secrets/permissions, Render deployment and live smoke tests, rollback/containment and actual provider receipts. User or professional involvement may still be required for storefront accounts, bank/tax settings, regulated transactions, and provider authorizations.

**Never say "done other than real-world proof" when automated integration tests or live deployment are also missing.** Report exact stages from docs/HEIMDALL_DEFINITION_OF_DONE.md.


## Additional required safety integration for all three passes

Read docs/PRIME_AUTONOMY_SAFETY_CONTRACT.md. Treat the new autonomy_governor.py as the first deterministic policy gate, not a complete deployed security subsystem. PASS 1 must verify the stored owner approval and durable global kill switch before any external operation, test malicious instruction injection and false evidence, add persisted unknown-outcome quarantine and circuit breaker state, and prove tenant/authority boundaries. PASS 2 must enforce confirmed permission, consent, cost limits and legal posting rights at actual external marketing, checkout, payout and customer-support adapters. PASS 3 must require evidence-checked, independent source-grounded evaluation with abstention, cross-agent verification, self-repair within narrow bounds, emergency stop, incident escalation, and performance metrics (owner escalations per 100 actions, double-write count, unsupported decisions, escaped governance checks). No LLM output can set its own approval boolean.


## New November 19/20 source and log audit — execute this before Pass 1

Read ops/REMAINING_SYSTEM_BLOCKERS_2026-11-19.md and the updated ops/CHANGE_LEDGER.md.

The current PR branch already proves canonical FastAPI route import (7/7 required routers, 9/9 required endpoints) and 85 focused tests, including real disposable PostgreSQL worker concurrency and additive Factory/WeWeb revocation migrations. Preserve that evidence and don't regress it.

CI backend pytest collection has two remaining historical mismatches: test_fake_live_operating_day now expects a nonexistent app.routers.system_self_check; test_system_integrity expects obsolete Deal/BuyerMatch model exports. Do not invent a fake anomaly endpoint or BuyerMatch ORM merely to get green collection. Reconcile the intended behavior with the actual canonical ORM, implement and test genuine functionality if required, or replace obsolete test cases with real acceptance tests.

Then execute the entire backend suite, not merely --collect-only, in an isolated environment. Record counts, failing tests, causes and exact fixes. Rehearse the full Alembic upgrade chain against a disposable production-like PostgreSQL schema, confirm live API DB identity without exposing secrets, and maintain a release/rollback plan.

The new auth_revoked_access_tokens table and core/database fail-closed behavior require migration-first deployment planning; attempting to deploy code before schema preparation can make active session APIs fail with HTTP 503. No production merge without explicit owner approval.


## Pass 0 and Pass 4: entire original Valhalla vision (mandatory scope)

**Pass 0 BEFORE engine work:** Read ops/VALHALLA_FULL_VISION_TRACEABILITY.md and the expanded 47-workstream ops/prime_system_integration_matrix.json. This full scope includes the named Gods/Bridge Layer, original five-god risk evaluators, Norns, Mimir, Commander/voice A/B/C/Override, five initial legacies, live clones vs simulation mirrors, Product/Venture Foundries, real estate, non-RE engines, 90/10 and private Fun Fund rules, corporate banking, infinite banking, family/estate trusts, Panama and Bahamas, Canada departure/residency, tax/legal opinions, family payroll, Black Ice and resort development.

Reconcile conflicting role/authority and trust-timing documents explicitly; do not choose a doctrine from documentation recency. Reuse real modules only and mark absent capabilities as absent.

**Pass 4 AFTER operating spine and revenue loop are safely proven:** Implement PRIVATELY scoped owner decision tools, not unauthorized cross-border/legal execution: (a) real insurer-illustration-based whole-life/policy loan scenario model including premiums, loans, cash-flow costs and downside, (b) corporate/treasury/fund separation and owner-controlled 90/10 policy and cap schedules, (c) professional-reviewed family trust/succession alternatives with ownership and trustee audit, (d) Canadian personal/corporate tax residency departure comparison and obligations, (e) Bahamas/Panama and other residency option matrices, (f) controlled family/staff payroll and external specialist review. Never claim that a trust record legally establishes a trust, a life insurance policy exists, tax residency is ended, or a bank transfer cleared from a stored row.

**Every Pass:** Report a 47-workstream diff of real evidence stages, missing source dependencies, production verification status, owner/professional approval requirements and unresolved prior agreements. The owner remains sovereign. No uncontrolled payments, registrations, filings, tax advice automation or real-life account changes.


## Loki is a separate mandatory independent-audit workstream

Before wiring production external effects, implement and integrate docs/LOKI_INDEPENDENT_CHALLENGER_CONTRACT.md. The current in-process universal_loki_objections and 18 Pantheon tests are beneficial deterministic checks but not independent stress-test inference. Legacy review placeholder success has been disabled. Missing/timeout/unsupported Loki audit must HOLD high-impact actions, and the audit must bind by checksum to a versioned Heimdall proposal. Require three adversarial test scenarios and review-after-edit proof. No self-issued clearance or model-generated provider receipts.

## Additional tested work from November 20

Preserve the newly implemented direct five-God dispatch, Prime control-key isolation, scoped shadow Mimir, corrected post-hard-gate predictions and standing internal-draft authority. Existing completion registry tests are now required CI. Read CODEX_START_HERE.md's November 20 update; do not recreate this work.

Pass 1 must wire securely separated credentials in all server-only callers and prove tenants cannot access Prime controls; no model/worker may obtain the mandate-grant key. No standing grant expands external authority. Preserve real transactional consumption/revocation and verify independently held audit receipt. Pass 2/3: build genuine system-wide recurring specialist report/decision pipeline, source-grounded independent Loki reviewer, real outcome learning, worker leases/recovery, and safe provider adapters using the same authority discipline. Pass 4 remains the original wealth/trust/infinite-banking/Canada-exit and family succession advisory scope. All 47 workstreams remain required, none silently removed.
