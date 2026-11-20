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
