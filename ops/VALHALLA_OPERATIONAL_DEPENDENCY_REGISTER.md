# Valhalla operational dependency register

Companion to the [operational audit](../docs/VALHALLA_AUTONOMY_OPERATIONAL_AUDIT.md). Tasks 04–53 correspond exactly to the 50 contracts. Cross-cutting tasks 01–03 remain in the [canonical task index](../docs/CODEX_RESUME_2026-12-01.md#current-workstream-index-and-startup-order) for full regression, reconciling checkout differences and one connected proof. Evidence stages and pass criteria below follow the [canonical integration matrix](prime_system_integration_matrix.json). The seven packages, P0 priorities, gates and existing contracts remain authoritative.

First-business impact assumes the bounded one-time CAD lane. It does not preselect that offer, settle which legal duties apply, or change the January P0 gates. “First scoped” means prove the applicable slice before day one. “Conditional” means causal to the selected business or interface. “Later model” means the contract still gates its own business model or broader expansion. Effort ranges are estimates for one operator's verification or coordination of one scoped case, excluding engineering, service fees or elapsed evidence collection. Shared work overlaps and should be counted once. All records remain open for independent operational evidence.

## Go Live reconciliation

The [owner readiness dossier](../docs/VALHALLA_FULL_GO_LIVE_READINESS.md) applies the current doctrine to all 50 contracts below. The mandated-duty lines clarify scope and accountable fallbacks. The original acceptance text and priority still govern. Required delegates and independent services remain launch dependencies wherever uncommissioned. Their absence holds the affected activity. The owner retains supervision, material exceptions and reserved approvals. No routine duty is assigned by default to the owner.

## First operating loop verification

The [disposable operating proof](../docs/VALHALLA_FIRST_OPERATING_LOOP.md) connects authorized signed source intake, exact event-driven ODIN and NJORD findings, independent Loki analysis and immutable material exceptions, Prime's automatic recommendation, one final mandate, and the acquisition/checkout/settlement/Mimir worker. A replacement source observation is re-reviewed. No routine owner action occurs after the final mandate. This is one scoped isolated integration case. Genuine external discovery, hosted recovery, provider operations and all production gates remain open. The [refund and bank acceptance contract](../docs/VALHALLA_REFUND_BANK_COMMISSIONING.md) records the next authorized provider steps.

### Launch-essential implementation checkpoint

**November 24 specialist and effect boundaries.** Distinct scheduled ODIN and NJORD workers now sign exact reports with Ed25519. [Worker identities](../services/api/app/pantheon/identity.py) require separate Prime and owner authentication to enroll a public worker key to one role, assignment, scope and short lifetime. A backend-only enrollment key signs the durable public authorization. Workers use the pinned enrollment public key and their own private key. Exact reports remain readable after revocation for audit, while current Prime reliance is denied. The source run checks the current signed evidence before review, decision, mandate and worker handoff. Independent Loki review remains mandatory. [Worker entry point](../services/api/tools/cron/pantheon_worker.py) · [Identity tests](../services/api/tests/test_pantheon_worker_identity.py) · [Source-to-outcome regression](../services/api/tests/operating_rehearsal_case.py)

| First-business boundary | Verified internal behavior and external gate |
|---|---|
| Acquisition, notification and CRM | [Outbox and raw messaging checks](../services/api/tests/test_shadow_side_effect_guards.py) deny transport before send and preserve existing queued work. The legacy CRM promotion endpoint returns held instead of claiming success. Live CRM promotion, consent-bound communication and independent provider confirmation remain unavailable. |
| Marketing and publication | The [publish register](../services/api/app/services/media_engine.py) already rejects a client assertion of published status. The [acquisition receipt](../services/api/app/services/acquisition_channel_fixture.py) is fixture-only and checks consent/suppression, scope and stop. A real opt-in channel, provider writer and independent receipt remain uncommissioned. |
| Agreements | [Queued legal email](../services/api/app/legal/legal_send_service.py) holds before loading or sending queued documents. The canonical contract pipeline allows only local sandbox envelopes, and [DocuSign](../services/api/app/integrations/docusign/client.py) already denies uncommissioned live sends. Real signatory authorization and provider acceptance remain open. |
| Checkout, fulfillment and support | [Stripe capture and delivery regression](../services/api/tests/test_product_artifact_workflow.py) proves signed ingress remains journaled, actual-byte delivery is gated, and the underlying tenant, acknowledgment and revocation checks still work in an isolated transport fixture. Live checkout/confirmation placeholders no longer return success. Recurring live checkout and cancellation hold, while the test-provider path rechecks stop before writes. Routine support is fixture-only. A commissioned seller, exact offer, consent and delegated customer support remain required. |
| Refund and finance | [Refund tests](../services/api/tests/test_stripe_finance.py) check scope withdrawal during provider readback, expiry, stop, lost response, persisted attempt, restart/replay and independent callback/readback. Live bank booking, reversals, corrections, revenue/liability release and cash availability hold. Genuine native sandbox/provider receipts, independent bank evidence and accountant acceptance remain outstanding. |

The active release remains a deny-all policy for live effects. Scoped positive release calculation and hosted worker access controls remain open. The [PostgreSQL worker regression](../tests/test_factory_postgres.py) uses real worker processes with disposable keys to test role substitution, receipt persistence and restart. Hosted commissioning must keep the registrar private key out of specialist workers, use separately permissioned database identities, and verify that a worker cannot change or delete enrollment, revocation or another worker's evidence. The two tested signing identities do not establish independent operation across the full Pantheon.

The legacy acquisition outbox now checks the same release blocker reported by the private briefing before opening SMTP or HTTP transports. Queued work remains available for audit with unchanged attempts and delivery state. A strict disposable source-run policy also makes Prime wait for exact ODIN and NJORD reports from the scheduled role entry point. It rejects records from inline execution when that policy is enabled. The report digest includes the execution path, and the exact report still requires independent Loki review. The recorded path identifies the code entry point. Independent hosted identities and process isolation require commissioning evidence.

The first bounded one-time CAD lane needs the applicable slices of `runtime_governance`, `legacy_execution`, `marketing`, `commerce`, `finance_webhooks`, `payouts_and_funds`, `pantheon_five_evaluators`, `pantheon_expanded_bridge`, `five_initial_legacies` (one selected slot), `treasury_banking_controls`, `loki_independent_challenger` and `dynamic_capital_allocation_loss_containment_and_strategic_redeployment` (caps and containment). `builder_code` is required if the offer needs a new governed artifact or release recipe. `prime_private_owner` retains private supervision requirements. The remaining attachment-analysis and startup-to-finance extension is conditional on that reliance path. Subsequent Legacy slots, recurring accrual and unsupported financial corrections remain gated for their own scope. A defined hold and delegated exception path is necessary for an unresolved correction in the first lane.

| Routine duty | Existing path and accountable fallback | Planning allowance for a bounded pilot exception |
|---|---|---|
| Acquisition and sales | Uncommissioned dispatch held. An approved partner or acquisition delegate executes only on an enrolled inbound channel after consent and channel acceptance. Record placement or prospect receipt and stop on suppression. | 1 h × CA$40–75 = CA$40–75 |
| Signing | Fixed approved terms can use scoped assent where accepted by qualified review. If an actual signature is required, send stays held pending an enrolled signatory or contract administrator with verified delivery and status. | 0.5–1 h × CA$45–90 = CA$22.50–90, plus separately quoted provider and legal fees |
| Fulfillment | Buyer-bound digital delivery and acknowledgment work in the disposable lane. A scoped fulfillment operator handles failed delivery and records the artifact digest, documented retry and buyer outcome. | 0.5–1 h × CA$35–75 = CA$17.50–75 |
| Support and refunds | Disposable routine resolution has worker receipts. A scoped support delegate handles verified customer cases and exceptions without permission to authorize funds beyond approved policy. | 0.5–1 h × CA$35–75 = CA$17.50–75 |
| Finance and reconciliation | Internal fixture reconciliation and cash holds work. An authorized bookkeeper reviews the processor/bank trace and escalates accounting treatment to an accountant. Cash stays held through unresolved differences. | 1–2 h × CA$55–100 = CA$55–200, plus separately quoted accountant and provider fees |

These are assumed Canadian-dollar planning rates and time per handled pilot exception, with no quotes, staffing or spending approved. Confirm written rates, coverage and caps before activation. A missing delegate leaves its lane held. The owner receives the material briefing and keeps reserved decisions.

## Verified learning checkpoint

- A signed source refresh dispatches the existing scoped specialty and Prime queues. Independent Prime verdicts now pin exact Foundry evidence IDs and digests. A revision report identifies the superseded evidence, changed declared assumptions and matched earlier verdicts. A scoped verdict stays held for reconsideration. Older verdicts without the new binding remain outside this reverse lookup. [Source regression](../services/api/tests/test_economic_control.py)
- The existing mandate and outcome records retain the forecast, deadline, costs, refund alternative and Norns contribution error. In the disposable full-refund run, expected contribution equals price less 175 CAD cents, observed contribution is negative 175 CAD cents, and the error equals negative price. Signed synthetic payment and bank receipts drive the calculation. The existing Mimir claim checks body digest, scope, source lineage and reconciled checkout evidence. [Connected regression](../services/api/tests/operating_rehearsal_case.py)
- A subsequent evaluation citing that exact Mimir proof holds the unchanged product version and price, with no effect on another version. Separately authenticated Loki challenges refund timing, retained revenue and cost assumptions. The result proposes testing a refund-adjusted approach. A prospectively enrolled independent holdout comparison for that economic playbook and genuine observed outcomes remain open. Existing Norns Factory deadline holdouts and Brier scores remain separate. No production strategy, financial or provider permissions are promoted.

### Prospective economic holdout and automatic reuse

- The [existing Foundry rehearsal](../services/api/app/routers/foundry_operating_rehearsal.py) stores the pre-observation plan and independently signed outcome in its existing event journal without adding transitions to the 31-receipt run. The [scorer](../services/api/app/services/foundry_holdout.py) compares both arms on net contribution, refunds, direct execution cost and worst case. The [connected test](../services/api/tests/operating_rehearsal_case.py) freezes three distinct paired cases and both versions before independent Loki and the fixture observer act. The original yielded CA$32.75 and the revised arm CA$35.20. Promotion was rejected even though the revised arm improved on these fixtures. The scorer also rejects adverse economics. Cases before plan or review, altered signatures, duplicates and reuse of the training ID are denied.
- Mimir and the existing [Prime evaluator](../services/api/app/routers/completion_registry.py) automatically recheck exact matching shortfalls for 30 days from completion. Review artifacts bind the retrieved digests. Prime holds the same version without caller-supplied claims, and a prior favorable snapshot does not bypass the current hold at dispatch. Different versions and scopes do not inherit results. Revocation leaves historical evidence readable. Stale source, damaged receipt and optional explicit duplicate or cross-Legacy claims are exercised.
- The existing Prime economic schedule receives a transactional learning wake-up on completion. The rehearsal reconnects to its database, verifies the same lesson caused HOLD before the next scheduled cadence, then replays the trigger and receives the original advisory receipt. These are locally verified synthetic evidence paths. Independent provider commissioning, real paired observations, legal and privacy rights, named reviewer and observer operators, and existing separately authorized release are required before any commercial reliance.

## 04. `api_wiring` (P0)

- **Mandated duty and operator boundary.** Register and check required APIs. Release integrator verifies deployed route and rollback.
- **Stage and source.** `FOCUSED_CI_TESTED`. Canonical FastAPI import registered 36 critical routers and all 95 required routes in the isolated runtime. [Primary source](../services/api/app/main.py).
- **Current evidence.** Canonical route probe verified all 95 required methods and paths. Canonical threshold CRUD and all seven historical CI5 tuning checks pass. Every tuning route rejects requests without the existing private Prime control identity. Disposable PostgreSQL verified the additive profile index preserves executable rule names and maintains separate profile identities across namespaces.
- **Internal next step.** No separately identified coding gap in the matrix. Add registered-route behavior coverage where only import routing is proven.
- **External and independent proof.** Run the route probe with migrated staging PostgreSQL. Exact commit, route probe and health receipts from the authorized staging runtime.
- **Authority and professional review.** Approve the staging runtime. No separate professional item identified.
- **Impact and accountable fallback.** An unreachable or miswired contract prevents correct dispatch. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Technical integrator holds release and restores known-good routes. Estimated effort 2–4 h.
- **Exact acceptance contract.** Prove every mandatory router imports in a clean canonical app; no missing OpenAPI paths or silent startup success
- **Next action.** Exercise the registered routes in an authorized staging environment with migrated PostgreSQL.

## 05. `auth` (P0)

- **Mandated duty and operator boundary.** Enforce scoped revocable identities. Identity operator handles proof, recovery and lock exceptions.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. WeWeb logout and refresh revocations moved from process-local memory into hashed persistent database records; owner reset now always requires configured secret. Login and refresh token responses are explicitly uncacheable. Disposable Chromium exercises the real owner and buyer login, private authorization and revoked bearer replay over loopback. SQLite tests pass. Other auth paths and production migration unverified. [Primary source](../services/api/app/routers/auth_weweb.py).
- **Current evidence.** See SQLITE_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** No separately identified coding gap in the matrix. Test every private write lane and role isolation with actual revocation.
- **External and independent proof.** Exercise fresh login, revocation and owner bypass-denial from the actual WeWeb Preview origin in authorized staging. Independently observed owner versus subscriber access denial and revoked sessions.
- **Authority and professional review.** Approve test accounts and credential rotation. No separate professional item identified.
- **Impact and accountable fallback.** An unverified identity can expose owner or buyer state. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Identity administrator revokes the affected session and holds access. Estimated effort 2–4 h.
- **Exact acceptance contract.** Persistent logout/revocation and RBAC across restart; ownership and tenant-bound denies; real login/logout smoke
- **Next action.** Verify scoped authorization, persistent revocation and fresh login on staging.

## 06. `runtime_governance` (P0)

- **Mandated duty and operator boundary.** Bound every side effect by mandate, risk, expiry and stop. Prime holds missing authority and escalates to the duty operator.
- **Stage and source.** `POSTGRES_INTEGRATION_TESTED`. Offline staging preflight checks approved private database binding, exact CORS, test-only Stripe and separation of Loki credentials. The worker launcher stays held by default. One internal draft execution lane uses persisted standing owner mandates, separate grant/worker authorization, exact scope, usage/expiry and revocation checks. Isolated SQLite and PostgreSQL one-use concurrency tests passed. Other dispatch paths, continuous full-system specialist coverage and provider effects remain unverified. [Primary source](../scripts/staging_preflight.py).
- **Current evidence.** See POSTGRES_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md. The alternate-root rehearsal rejects a cross-currency reservation reviewed before a hold and refuses a newly reviewed proposal while that hold remains. A new accounting identity cannot book opening commitments to evade it.
- **Internal next step.** Apply the canonical gates to remaining dispatch lanes. Factory, fulfillment and economic booking share business-wide holds across operating roots and currencies. Exercise denial, rollback and emergency recovery on each path.
- **External and independent proof.** Rehearse long-running governance recovery. Scoped governed worker logs, emergency-stop receipt and recovery without unauthorized effects.
- **Authority and professional review.** Authorize scoped worker activation. No separate professional item identified.
- **Impact and accountable fallback.** No verified stop or mandate means no authorized dispatch. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Prime holds write paths and a technical operator reconciles in-flight work. Estimated effort 2–4 h.
- **Exact acceptance contract.** Governance unit cases and internal SQLite Factory killswitch pass; full production acceptance requires every external adapter using trusted persisted approval/consent/budget gates, adversarial agent tests, durable circuit breakers, and real Postgres worker failure injection.
- **Next action.** Extend hard gates to remaining operating routes and rehearse recovery after governance denial.

## 07. `discovery_sources` (P1)

- **Mandated duty and operator boundary.** Discover and refresh lawful source evidence. Rights reviewer resolves ambiguous provenance, Prime queues routine research.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Durable local demand and procurement exports now accept owner-enrolled Ed25519 source signatures and enforce timestamp, replay, source rights and freshness checks. No outbound licensed feed has been activated. [Primary source](../scripts/ingest/ingest_sources.py).
- **Current evidence.** test_economic_control.py exercises a valid signed source, timestamp rejection, tampering, deduplication and the scoped Odin to Prime rehearsal. Product Foundry continuous fixture links signed discovery, independent challenge, scoped execution, outcome, retained losses and a subsequent HOLD with contradiction evidence. Operating diligence now attaches approved and dated references to exact Foundry versions, with specialist wake-up and Loki challenge. See the [Manitoba comparison and reproducible test](../docs/UNIVERSAL_OPPORTUNITY_PIPELINE.md#operating-diligence-and-first-investigation).
- **Internal next step.** Extend independent comparison across licensed source types. Verify expiry, rights and low-sample coverage for each connector.
- **External and independent proof.** Use an approved outbound-free staging export. Original dated source, terms or data rights, coverage, and independently observable demand.
- **Authority and professional review.** Approve source rights and data scope. No separate professional item identified.
- **Impact and accountable fallback.** Untrusted or expired sources leave discovery inconclusive. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Heimdall queues rights-reviewed research and abstains. Estimated effort 1–3 h.
- **Exact acceptance contract.** On schedule, acquire permissible fresh independent sources with attribution and dedupe; fail on revoked/expired rights
- **Next action.** Connect one approved outbound-free staging export connector and prove licensed, fresh demand evidence.
- **Conditional future work.** Scale connector coverage after proven demand.

## 08. `universal_evaluator` (P1)

- **Mandated duty and operator boundary.** Compare and reject opportunities with incomplete economics. Prime abstains, specialist reviews material unknowns.
- **Stage and source.** `FOCUSED_CI_TESTED`. Existing completion-registry suite now required in CI and passed; generic proposal rejects inconsistent margin/capital, snapshots final recommendation after risk gates, and reports Tyr/Forseti independent checks NOT_VERIFIED. Supplied candidates only; no autonomous discovery or external execution proved. [Primary source](../services/api/app/services/universal_opportunity_evaluator.py).
- **Current evidence.** See FOCUSED_CI_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md. Product Foundry continuous fixture links signed discovery, independent challenge, scoped execution, outcome, retained losses and a subsequent HOLD with contradiction evidence. The scoped acquisition fixture verifies debt stress, separately reviewed simulation, receipt reuse, revocation and reevaluation. SaaS, service and real-estate rehearsal covers shared stress rules, projection differences and simulated review. A repeated withdrawal queues one digest-bound event for opted-in Prime schedules and participating specialists. Prime switches to HOLD before cadence and the source is excluded from allocation.
- **Internal next step.** Extend source-weighted comparisons and typed claims beyond current artifacts and statements. Compare decisions across supported engines and missing or contradictory evidence.
- **External and independent proof.** Validate with externally sourced scoped evidence. Comparable source-backed price, cost, capital and demand evidence.
- **Authority and professional review.** Approve permitted inputs and test limits. No separate professional item identified.
- **Impact and accountable fallback.** Unsupported economics or missing constraints invalidate ranking. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Heimdall abstains and schedules missing diligence before selection. Estimated effort 1–3 h.
- **Exact acceptance contract.** Cross-industry cases produce repeatable evidence-locked predictions; unknown candidates yield abstention, not artificial opportunity
- **Next action.** Expand source-weighted comparative evidence and stage legally scoped evaluator dependencies.

## 09. `knowledge` (P1)

- **Mandated duty and operator boundary.** Retrieve versioned sources without scope leakage. Curator verifies licence, corrects stale sources and can revoke.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Knowledge and source governance registry code exists; freshness/permission runtime propagation unverified [Primary source](../services/api/app/routers/completion_registry.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Propagate source lifecycle changes through each actual consumer. Verify freshness, revocation and contradiction with independent sources.
- **External and independent proof.** Re-read licensed staged sources. Authoritative source copy, retrieval date and independent contradiction or revocation evidence.
- **Authority and professional review.** Approve sources and evidence rights. No separate professional item identified.
- **Impact and accountable fallback.** Stale or unscoped records corrupt downstream decisions. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Mimir quarantines the source and holds dependent reuse. Estimated effort 1–3 h.
- **Exact acceptance contract.** Bad/injected/stale sources blocked from live decisions; citations, correction version and expiry enforced
- **Next action.** Exercise source lifecycle revocation and conflict propagation across actual specialist consumers.

## 10. `learning_mimir` (P1)

- **Mandated duty and operator boundary.** Learn and reuse separately verified outcomes. Prime rejects stale or simulated evidence for real decisions.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Existing exact scoped evidence remains intact. Owner decisions can carry purpose, rationale and scoped dependencies, and recent differing statements under the same topic trigger a review flag. Provider-backed learning and semantic contradiction analysis remain open. [Primary source](../services/api/app/routers/legacy_playbooks.py).
- **Current evidence.** Factory reconciliation verifies Mimir outcome receipts against current scoped artifacts. The isolated owner desktop demonstration recalls a synthetic registry note as provisional evidence. The canonical Mimir migration now creates the knowledge registry on empty PostgreSQL and preserves existing records during application rollback and re-upgrade. Hosted acceptance remains open. Prime and Mimir can revalidate the exact delayed trigger beyond the recent 20-outcome window. Prime compares structured outcome claims with the exact current proof before allowing them into a decision. The private owner decision view and the Factory boundary revalidate a persisted claim before presenting or consuming it. The integrated rehearsal detects an altered learning receipt and recovers after restoring the original evidence. test_owner_conversation.py exercises rationale, visible dependencies, owner scope and repeated-topic conflict recall. Product Foundry continuous fixture links signed discovery, independent challenge, scoped execution, outcome, retained losses and a subsequent HOLD with contradiction evidence. The scoped acquisition fixture verifies debt stress, separately reviewed simulation, receipt reuse, revocation and reevaluation. Prime can verify scoped treasury statement fixture claims against current statement balance and digest. They provide zero proof of actual accessible funds. Prime accepts an exact scoped economic performance fixture and rejects altered results, wrong-jurisdiction reuse and attempts to mark it as a real-world outcome. Prime can revalidate and cite an exact resolved ordinary-cohort Norns deadline forecast. Holdouts, modified labels and mismatched scopes are excluded from decision evidence. The integrated Factory-to-Mimir-to-playbook test records measured successful deterministic execution and verifies the current evidence-backed baseline and its withdrawal after evidence corruption.
- **Internal next step.** Extend structured claim verification beyond Factory, scoped statements and the Economic Control performance journal. Bind an exact current playbook use to authorized execution and compare observed costs, latency, failures and validated outcomes. Historical successful draft samples alone do not measure reuse. Exercise damaged, superseded and delayed proof per class.
- **External and independent proof.** Rehearse backlog recovery and independent outcome lineage. Independently generated outcome receipts for production evidence classes.
- **Authority and professional review.** Authorize commissioned evidence scope. No separate professional item identified.
- **Impact and accountable fallback.** Unverified outcomes cannot improve the next decision. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Mimir retains the attempt separately and withholds reuse. Estimated effort 2–4 h.
- **Exact acceptance contract.** Record actual verified outcomes in PostgreSQL and prove replay correction without holdout leakage
- **Next action.** Extend structured claim verification to other evidence classes and rehearse backlog recovery in staging.

## 11. `legacy_instances` (P0)

- **Mandated duty and operator boundary.** Register isolated Ledgers and Legacies. Technical delegate enrolls authorized scope.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Policy-managed Legacies revalidate live policy during admission and recovery. A recorded recovery remains blocked until the owner approves its exact current receipt and synchronized policy. Factory group enrollment is atomic and scoped to finite internal-draft mandates. [Primary source](../services/api/app/routers/completion_registry.py).
- **Current evidence.** Disposable SQLite rehearsed failover, policy drift, emergency hold, stale receipt denial, rejected group rollback, enrollment and verified internal draft. PostgreSQL Factory and migration suites passed.
- **Internal next step.** No separately identified coding gap in the matrix. Rehearse restart and registry segregation on disposable migrated PostgreSQL.
- **External and independent proof.** Enroll the selected startup scopes in staging, commission authorized Legacy workers and record scoped recovery and execution receipts. Owner-approved mandate identity and real isolated restart, restore and registry receipts.
- **Authority and professional review.** Select initial mandates and jurisdictions, approve mandate limits, and authorize staging. No separate professional item identified.
- **Impact and accountable fallback.** Missing tenant context leaves jobs without operating authority. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Integrator quarantines the scope and Prime holds all side effects. Estimated effort 1–2 h.
- **Exact acceptance contract.** Two isolated legacies may not see or steal each other's tasks; identity/policy and failover tests pass
- **Next action.** Commission owner-approved Legacy scopes using the reviewed recovery receipt and group enrollment already implemented.
- **Conditional future work.** Additional regions follow viable operation.

## 12. `legacy_execution` (P0)

- **Mandated duty and operator boundary.** Dispatch legal business work and recover exactly once. Operator owns unsupported transitions and stalled cases.
- **Stage and source.** `POSTGRES_INTEGRATION_TESTED`. Single internal listing-draft lane and verified database receipts work in SQLite and disposable PostgreSQL. A finite, expiring, revocable standing internal-draft mandate passed SQLite tests and a real PostgreSQL two-worker one-use cap test. No provider execution, crash recovery or autonomous revenue proved. Internal lane now reconciles concurrent submissions, skips waiting/blocked entries, and passes PostgreSQL injected rollback and lost commit acknowledgement tests. Not generalized process-kill/provider recovery. [Primary source](../services/api/app/services/prime_business_execution.py).
- **Current evidence.** See POSTGRES_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Extend execution proof and independent receipts to approved operating adapters. Exercise each new adapter and emergency hold.
- **External and independent proof.** Commission first authorized operating lane. Independent outcome for each commissioned adapter, with mandate and exact action identity.
- **Authority and professional review.** Approve adapter and authority limits. No separate professional item identified.
- **Impact and accountable fallback.** Owner or fixture calls still bridge routine steps. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Prime holds unimplemented transitions and escalates exceptional execution to a delegated operator. Estimated effort 3–6 h.
- **Exact acceptance contract.** Real PostgreSQL task lifecycle survives restarts and duplicates; every completed status has independently verified receipt
- **Next action.** Exercise dispatch and verified outcomes on the first authorized operating adapter. Draft enrollment and post-recovery execution use the existing Factory lane.

## 13. `schema_and_migrations` (P0)

- **Mandated duty and operator boundary.** Apply compatible migrations and restore evidence. Release operator verifies restore target and schema.
- **Stage and source.** `POSTGRES_INTEGRATION_TESTED`. Prepared additive Factory and JWT revocation migrations; both upgraded and reran idempotently on disposable PostgreSQL with preexisting data preserved. Not complete historical chain or Render staging migration. [Primary source](../alembic/versions/20261119_factory_legacy_work_schema.py).
- **Current evidence.** PostgreSQL migration chain preserved prior attachments and required content or a tombstone, with inconsistent states rejected.
- **Internal next step.** No separately identified coding gap in the matrix. Exercise complete chain and backup restoration with representative data.
- **External and independent proof.** Run full migration and restore drill in staging. Exact revision and authorized staging backup/restore receipt.
- **Authority and professional review.** Approve disposable staging and backup policy. No separate professional item identified.
- **Impact and accountable fallback.** Schema or restore mismatch threatens durable operations. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Release operator blocks rollout and restores to the approved isolated target. Estimated effort 2–4 h.
- **Exact acceptance contract.** Rehearse upgrade and no-data-loss on disposable PostgreSQL; verify exact prod DB, heads and release rollback
- **Next action.** Rehearse the full deployment migration at staging scale and check restoration from backup.

## 14. `scheduling` (P0)

- **Mandated duty and operator boundary.** Schedule routine autonomous work persistently. Duty operator responds to lease alarms.
- **Stage and source.** `POSTGRES_INTEGRATION_TESTED`. Durable Prime and Pantheon event queues deduplicate independent triggers and preserve transactional worker recovery. Legacy pending columns remain a transition reader. [Primary source](../services/api/tools/cron/daily_email_ping.py).
- **Current evidence.** Disposable PostgreSQL verifies the migration, exclusive due work, simultaneous specialist sources, rollback and idempotent Prime wakeups. Canonical API fixtures cover missed work, independent trigger queues and replay.
- **Internal next step.** No separately identified coding gap in the matrix. Rehearse long outage, expiry and restart under sustained multirole workload.
- **External and independent proof.** Run authorized persistent workers with real host and credentials. Observed scheduled slots and measured recovery over an actual staging window.
- **Authority and professional review.** Approve staging workers and run window. No separate professional item identified.
- **Impact and accountable fallback.** Unmanaged scheduling loses work or repeats an effect. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Duty operator suspends workers and Prime reconciles leases and receipts. Estimated effort 2–4 h.
- **Exact acceptance contract.** Approved task executes on schedule, with exact host/credential controls; logs show durable receipt and no double issue
- **Next action.** Rehearse sustained authorized staging workers, missed work, expiry and restart recovery.

## 15. `builder_code` (P0)

- **Mandated duty and operator boundary.** Generate and test governed improvements. Builder submits scoped changes to separate release reviewer.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Isolated assignments, verified review exports and offline packages carry a selected GitHub draft target and locally tracked development head. Governed recipe expansion and actual GitHub commissioning remain open. [Primary source](../scripts/builder_assignment_worker.py).
- **Current evidence.** test_builder_assignments.py exercises lease reclaims, exhaustion, terminal status and stale receipt handling. The exact passing snapshot yields an owner-only, checksummed review packet. Recovery, wrong review input and emergency stop are exercised. Offline review materialization refuses a changed Git HEAD or mismatched receipt. An owner-authorized preparation can now group bounded file replacements into one pinned lease. Builder can generate the private owner-briefing collection from its named recipe after checking the source digest and registered GET routes. A second governed recipe repairs the metrics collection using the same review lease and its existing telemetry cache policy. Stale or duplicate targets leave no task or receipt. The materializer uses committed Git blobs for its checksummed diff and refuses dirty replacement bytes or additions already tracked at the passing base. A valid diff passes git apply --check in a disposable repository. An offline target-bound manifest verifies the repository, tracked head and patch, rejects mismatches and carries no submission or release authority. Disposable Git fixtures prove exact independent draft readback, digest pinning, denial for a non-draft PR and rejection of changed committed candidate bytes.
- **Internal next step.** Extend governed candidate recipes. The exact read-only GitHub submission verifier is implemented and needs the commissioned reviewer and a separately approved real candidate. Verify failure, stale base and review handoff for each recipe.
- **External and independent proof.** Commission a distinct runner and submission identity. GitHub readback matching exact reviewed commit, candidate digest and separate reviewer.
- **Authority and professional review.** Approve exact repository, branch, reviewer and write scope. No separate professional item identified.
- **Impact and accountable fallback.** Without governed Builder changes, releases depend on manual work. Blocks the first business if the selected model, interface or escalation needs it. Defer unused branches and keep them disabled. Integrator holds release while a separate code reviewer evaluates the patch. Estimated effort 2–4 h.
- **Exact acceptance contract.** Prove authorized durable development assignments, snapshot-bound artifact export, isolated fresh checkout and actual regression/security tests, scoped PR review and staged release. No API mutation of running source or unrestricted pushes.
- **Next action.** Extend governed candidate recipes and commission a distinct runner and approved review-only GitHub workflow.

## 16. `ai_providers` (P1)

- **Mandated duty and operator boundary.** Bound inference identity, purpose, cost and fallback. Provider administrator commissions approved model and retention.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Dated owner-attested quotes, role benchmark evidence, exact synthetic usage reconciliation and a budget-ranked staging candidate are recorded. Loki candidates exclude the active Prime model. External catalog discovery, provider billing and live suitability are pending. [Primary source](../services/api/app/routers/provider_pricing.py).
- **Current evidence.** See SQLITE_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Complete cross-role provider evidence and quota coverage where missing. Exercise quota, failure, independent identity and receipt verification.
- **External and independent proof.** Run individually authorized synthetic staging requests. Provider-issued isolated request, usage and cost evidence and independent Loki identity.
- **Authority and professional review.** Approve endpoint, model scope and limits. No separate professional item identified.
- **Impact and accountable fallback.** Missing model/calibrated authority limits inference. Blocks the first business if the selected model, interface or escalation needs it. Defer unused branches and keep them disabled. Prime uses valid deterministic evidence and holds inference-dependent decisions. Estimated effort 1–3 h.
- **Exact acceptance contract.** Select provider, enforce budget and data privacy, record cost, handle expired key/outage, optionally local model
- **Next action.** Exercise scoped benchmark, cost and quota enforcement with approved staging transport.
- **Conditional future work.** Provider expansion follows funded quotas.

## 17. `marketing` (P0)

- **Mandated duty and operator boundary.** Create and operate permitted customer campaigns. Heimdall needs a commissioned channel and operator to handle exceptions.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Private simulation binds a demand-backed plan before campaign visits and reconciles the attributed capture, refunds, delivery, costs and settlement. Direct-opt-in visits require exact scoped synthetic consent receipts. Roles can read the settled fixture and recommend pausing. Current demand evidence can also carry aggregate consumer motivations, objections, trust, regional fit and descriptive price-test uncertainty into a digest-bound candidate and campaign. Independent Loki flags overreach and changes in evidence. Per-scope synthetic suppression blocks new attribution across campaigns, deduplication prevents repeated attribution within a campaign, and settled comparison distinguishes stop, improve, keep testing and scale review with an independently challengeable artifact. The reviewed comparison records conservative simulated capital headroom against the current economic mandate. Pantheon reads the exact receipt as historical evidence. The internal channel adapter accepts signed synthetic receipts for reviewed, scoped and scheduled media intents; it never marks content published. Live publishing, actual audience consent and verified paid-order attribution are pending. [Primary source](../services/api/app/routers/foundry_checkout.py).
- **Current evidence.** See SQLITE_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Extend consent- and scope-bound rehearsal paths. Prove deduplication, suppression and attribution recovery.
- **External and independent proof.** Verify one approved channel with independently sourced attribution. Rights and consent provenance, provider receipt, and independently observed attributed conversion.
- **Authority and professional review.** Approve channel, recipients and consent basis. No separate professional item identified.
- **Impact and accountable fallback.** Uncommissioned channels prevent independent acquisition. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Heimdall drafts and holds dispatch while the authorized channel operator checks consent and provider limits. Estimated effort 2–5 h.
- **Exact acceptance contract.** True platform authenticated publish and provider receipt, lawful scheduling/consent, click attribution to paid order
- **Next action.** Verify consent, targeting and demand using an approved channel and independently sourced attribution.
- **Conditional future work.** Paid campaigns require separate budget.

## 18. `media` (P1)

- **Mandated duty and operator boundary.** Prepare and publish licensed content under delegated terms. Content rights and channel operator verify clearance.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Media channel/content records exist; false published status blocked; no real video/social publisher integrated [Primary source](../services/api/app/routers/media_engine.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Bind reviewed content to exact publishing intent and returned receipt. Test denied, replayed and withdrawn publication evidence.
- **External and independent proof.** Verify one authorized provider sandbox receipt. Dated rights and approved destination; exact external publish receipt only for authorized actions.
- **Authority and professional review.** Approve rights, destination and publication scope. No separate professional item identified.
- **Impact and accountable fallback.** Unlicensed media or publication paths block creative delivery. Blocks the first business if the selected model, interface or escalation needs it. Defer unused branches and keep them disabled. Authorized content operator verifies rights and holds publication. Estimated effort 1–3 h.
- **Exact acceptance contract.** Produce final legal asset, publish with provider confirmation, match URL and verified account, update audit history
- **Next action.** Bind reviewed content to an independently verified authorized publishing receipt.

## 19. `subscription_saas` (P1)

- **Mandated duty and operator boundary.** Operate paid SaaS renewals, tenant isolation and cancellation. Subscriber support delegate is required for unresolved access or billing.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Prime and owner authorization protect administrative mutations. Internal revocable WeWeb trial access binds account, tenant, plan, expiry and permitted module. Paid entitlements and tenant-bound engine data paths are pending. [Primary source](../services/api/tests/test_saas_tenant_entitlements.py).
- **Current evidence.** See SQLITE_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md. SaaS, service and real-estate rehearsal covers shared stress rules, projection differences and simulated review. A repeated withdrawal queues one digest-bound event for opted-in Prime schedules and participating specialists. Prime switches to HOLD before cadence and the source is excluded from allocation.
- **Internal next step.** A private subscriber can now enumerate only their own bound subscriptions with current paid, cancellation and recovery state. The primary editor inventory, pagination and completed-period acknowledgment were saved and replayed in isolation. Complete broader subscriber support and module-specific entitlement renewal and revocation gaps. Prove billing event replay and tenant isolation for chosen modules. With authorized staging, check primary editor pagination across multiple pages and completed-service acknowledgment as exact, revoked and cross-tenant buyers.
- **External and independent proof.** Verify approved sandbox billing events. Exact signed invoices, processor readback, and independently observed entitlement and cancellation receipts.
- **Authority and professional review.** Select modules and approved merchant sandbox. No separate professional item identified.
- **Impact and accountable fallback.** Uncommissioned renewals can break access and recurring cash controls. Defer for the first bounded commerce lane. Blocks autonomous operation of this domain when selected. Subscription support provider verifies rights and pauses entitlement changes on contradictory evidence. Estimated effort 3–6 h.
- **Exact acceptance contract.** Real checkout subscription grants scoped rights, renewal/payment failure revokes, subscriptions isolated from Prime
- **Next action.** Prove tenant scoping, billing events, entitlements, activation and revocation in the chosen modules.
- **Conditional future work.** Paid rollout follows operating approval.

## 20. `commerce` (P0)

- **Mandated duty and operator boundary.** Operate checkout, order, delivery, returns and support. Commerce exception operator owns unsupported disputes and holds.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. The native CAD one-time and fixed monthly recurring paths use independently checked Stripe identities under existing scope and buyer controls. The isolated recurring worker reconciles signed paid invoices, retries unavailable readback and preserves contracted access on failed renewals or period-end cancellation. The primary editor has a session-bound subscriber billing panel. One-time CAD partial refund corrections enforce a strictly increasing signed cumulative amount and unique processor transaction. The hosted staging environment denies synthetic one-time delivery acknowledgment at the API; local synthetic acknowledgment remains a fixture-only path. The dual-key sandbox payment plan derives exact buyer and tenant metadata from a current scoped listing and rejects bound orders, inactive identities and a held checkout. Its returned plan is a projection with no money or provider authority. Scoped Pantheon and Prime observations carry intact recurring periods and Loki challenges contradictions. Recurring gross, fees, net and exact payout membership use canonical independently checked processor receipts. Exact recurring invoice members use the existing whole-payout bank reconciliation and guarded liability posting path. Single-period recurring service recognition, exact CAD partial and full refund correction and bounded lost-dispute correction are implemented. The primary editor has inventory pagination and exact completed-service acknowledgment. Cross-period accrual, unsupported corrections, independent cash evidence and actual browser and provider commissioning remain open. [Primary source](../services/api/app/services/stripe_recurring.py).
- **Current evidence.** The private checkout rehearsal proved reviewed partial support closure and scoped Prime-only routine closeout of an exact full refund reconciled to the signed fixture journal. Denial covers an invalid Prime key, a foreign scope, partial refunds, the disabled flag, hosted staging and emergency stop. The digest binds the fixture actor and exact replay preserves one receipt. No external refund or communication occurs. The checkout rehearsal verifies a paid delivery hold, reviewed retry, emergency stop, idempotent retry and subsequent signed refund support. The Stripe sandbox browser gate requires denial of product bytes and acknowledgment. Positive paid delivery and acknowledgment currently have an isolated in-process fixture only. SaaS rejects fixture references on activation and access checks, including previously stored fixture references. Legacy SaaS records tagged with unverified provider references cannot grant access. New provider-tagged requests are pending verification, and tracked manual subscriptions remain available. Held fulfillment and unresolved refund support now cause scheduled Prime to HOLD. They also surface in specialist evidence routed to Loki. The checkout rehearsal asserts that Prime can identify a fulfillment hold with settlement tables absent, preserving capture as unreconciled. The completed synthetic order now yields a digest-bound closed-checkout proof joining Mimir listing lineage, full capture, delivery, refund support, costs and the independently matched statement postings. Economic booking and later Mimir verification check the exact scope, totals, period and current proof. An altered receipt removes simulated exposure headroom and is surfaced to Prime and independent Loki.
- **Internal next step.** One-time buyer-bound delivery and guarded liability release are implemented. The bounded fixed-price CAD subscription lane implements native Checkout, paid periods, retry and cancellation. Completed recurring paid service can release an exact settled liability within one open period. Exact recurring refund correction, buyer-scoped inventory pagination and completed-service acknowledgment are implemented. Complete autonomous payout-to-bank reconciliation, cross-period accrual, unsupported adverse outcomes and broader fulfillment, entitlement and recovery coverage. Exercise disputed cost fixtures, duplicate provider events, recurring account reversal and cross-product entitlement denial.
- **External and independent proof.** Run approved storefront lifecycle in staging. Independent payment capture, buyer receipt, item entitlement, payout and correction documents.
- **Authority and professional review.** Approve listings, rights, support and merchant scope. Qualified accounting or legal review of revenue and obligations when required by the chosen offer, jurisdiction or reliance decision.
- **Impact and accountable fallback.** Missing connected payment, fulfillment or support blocks commerce. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Prime holds scope and the support delegate handles exceptions. Estimated effort 3–6 h.
- **Exact acceptance contract.** Real approved listing/checkout/delivery/refund, buyer rights and content-hash verified, receipt tied to business
- **Next action.** Run the first authorized storefront lifecycle with support, costs and independently matched settlement receipts.
- **Conditional future work.** Real sales follow commercial approval.

## 21. `finance_webhooks` (P0)

- **Mandated duty and operator boundary.** Journal genuine provider events and deny duplicates. Payment duty operator handles contradictory signed/provider data.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Signed local capture and refund deltas can reconcile with unique scoped statement-fixture entries. Mismatches show the exact difference and cannot attach a settlement receipt. The canonical Stripe ingress can journal signed events in an explicitly enabled matching mode. Restricted readback can correlate exact product, capture, processor balance and payout membership. The same-scope CAD positive-capture path supports independent bank trace matching and guarded liability booking. Exceptions, actual commissioning and lifecycle accounting remain pending. [Primary source](../services/api/app/integrations/stripe/__init__.py).
- **Current evidence.** test_product_artifact_workflow.py exercises exact matches, difference reporting and bound-receipt replay in an integrated checkout. test_stripe_finance.py exercises signed canonical ingress and exact account, order, charge and balance linkage with synthetic upstream transport.
- **Internal next step.** Signed event journaling, one-time CAD full and ordered partial corrections, and exact recurring processor balance are implemented. Full and partial terminal lost one-time and recurring CAD chargebacks with one exact principal and fee movement have a guarded correction path, including after recognition. Paired readback of a supported full CAD payout reversal and independent bank debit has a guarded correction path. Recurring CAD refunds reuse ordered exact processor corrections for one bank-settled invoice. New partial-refund IDs fit the existing PostgreSQL column and use the original global processor-transaction uniqueness guard. Earlier receipts in stores that accepted the old IDs retain exact replay and cumulative ordering. Signed dispute update, funds-withdrawn and reinstatement events now preserve holds for the exact charge. A newer or unorderable contradictory signal prevents lost-dispute correction. A timestamped signed win or reinstatement can now correct one previously accounted CAD dispute using independent readback of the exact debit and reinstatement credit. The guarded correction preserves the original entries, current accounting hold and independent bank requirement. Won cases without a prior accounted debit, failed or adjusted payouts, cross-invoice disputes and multi-adjustment corrections remain open. Local backend regression verified partial recurring loss, over-capture refusal, exact-once processor correction, balanced post-recognition entries and retained scope holds. Recurring refund tests cover signed cumulative ordering, wrong invoice and buyer refusal, balance mismatch, replay and post-release hold. Synthetic recurring tests also prove a funds-withdrawn-only event holds settled receipts, older review events allow a subsequent exact loss, and newer appeal or reinstatement refuses stale loss. Replay native commissioning fixtures for remaining adjustments and settlement reversals.
- **External and independent proof.** Verify named sandbox event stream and separately sourced settlement. Authenticated provider and bank records for capture, reversal and payout reconciliation.
- **Authority and professional review.** Approve sandbox credentials, callbacks and side effects. Qualified accountant reviews the applicable chart, liability and correction posting rules before relying on live entries.
- **Impact and accountable fallback.** An unverified callback may create false payment or accounting state. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Finance operator quarantines callbacks and reconciles provider references. Estimated effort 2–4 h.
- **Exact acceptance contract.** Signed timestamped webhooks idempotently persist, settle, reverse, reconcile Stripe/Payhip events; provider receipt
- **Next action.** Connect the canonical Stripe financial event consumer to exact order, entitlement and ledger receipts, then verify the authorized sandbox event stream and separately sourced settlement.

## 22. `payouts_and_funds` (P0)

- **Mandated duty and operator boundary.** Match independent settlement and preserve cash restrictions. Authorized finance operator and accountant handle discrepancies.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Unimplemented payout creation fails closed. Read-only Stripe payout membership can bind an independently retrieved processor receipt to an exact scoped capture. [Primary source](../services/api/app/banking/plaid_transactions.py).
- **Current evidence.** test_stripe_finance.py rechecks signed orders and exact automatic payout membership with isolated HTTP and SQLite. It refuses a wrong destination, absent or altered membership, and a reversed payout. This verifies the processor readback slice only.
- **Internal next step.** Processor payout membership is checked for exact automatic Stripe payout and capture. Bank trace matching and guarded same-scope batch booking are implemented for CAD with no payout adjustments. Complete adjustment and reversal accounting, available cash and owner-mandate enforcement for actual funds. Extend contention and closed-period rehearsals for same-scope bank adjustments, duplicate correction and payout-intent denial.
- **External and independent proof.** Commission approved sandbox with reusable receipt proof. Independent processor payout and account-specific bank trace, liabilities and authorized funding receipt.
- **Authority and professional review.** Approve provider and allowed authority. Qualified banking or accounting review verifies bank authority, funds restrictions and applicable posting treatment.
- **Impact and accountable fallback.** A provider payout alone cannot clear the cash hold. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Accountant or banking operator obtains independent deposit evidence and keeps funds restricted. Estimated effort 2–5 h.
- **Exact acceptance contract.** No transfer without owner limit; provider payout id and settlement reconciled; no fabricated in_transit state
- **Next action.** Prepare verified settlement adapters and owner-mandate validation before any payout.
- **Conditional future work.** Live payouts require reconciled funds and distinct consent.

## 23. `contracts_legal` (P1)

- **Mandated duty and operator boundary.** Prepare, negotiate and bind approved agreements. Authorized representative or licensed adviser signs when applicable.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Contract template and document routes exist; actual external signature/legal approvals unproven [Primary source](../services/api/app/routers/contracts.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md. Private owner startup comparison separates dated public fees, quote and estimate classes, unknowns, activation, reserves and runway.
- **Internal next step.** Finish scoped review intake and bind approved terms to internal drafts. Exercise unsigned, wrong-party and superseded terms.
- **External and independent proof.** Commission exact DocuSign test envelope and recipient readback. Callback authentication and write authority remain separate. Independent envelope readback, parties and audited signing receipt.
- **Authority and professional review.** Choose the agreement, qualified reviewer and exact approved test signing scope. Licensed counsel reviews actual terms and filings when the selected activity requires it.
- **Impact and accountable fallback.** Absent authority or signed proof blocks binding agreements. Blocks the first business if the selected model, interface or escalation needs it. Defer unused branches and keep them disabled. Qualified counsel or a designated signing representative handles exceptions while agreements are held. Estimated effort 1–3 h plus provider quote.
- **Exact acceptance contract.** Jurisdiction and licensed review gates; provider envelope true signed-event receipt and revocation evidence
- **Next action.** Prepare provider contracts and professional review intake before execution.
- **Conditional future work.** Live agreements need separate approval.

## 24. `real_estate_execution` (P1)

- **Mandated duty and operator boundary.** Support governed property acquisition, sales and servicing. Licensed and field operators cover regulated and physical steps.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. SQLite regressions cover audited deal stages, transactional intake, explicit deal-to-brief linkage, underwriting freezes and a controlled operating-day rehearsal. External closing, payment and market-specific outcomes remain unverified [Primary source](../services/api/app/routers/execution.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Complete legally scoped practice stages and exact evidence linkage. Exercise approvals, adverse outcomes and jurisdiction denials.
- **External and independent proof.** Run authorized provider sandbox where selected. Current listing or comparables, rights, due diligence and actual practice transaction evidence when authorized.
- **Authority and professional review.** Select the jurisdiction and authorize the exact practice scope. Qualified jurisdictional review of transaction boundaries and applicable duties.
- **Impact and accountable fallback.** Real estate execution depends on licensed and on-site steps. Defer for the first bounded commerce lane. Blocks autonomous operation of this domain when selected. Licensed broker, counsel or property operator handles those steps, with the transaction held during gaps. Estimated effort 4–8 h initial coordination plus transaction quotes.
- **Exact acceptance contract.** Intake-to-deal-to-contract-to-payment simulation then lawful real deal using canonical work lifecycle
- **Next action.** Exercise a complete legally scoped practice transaction and documented approvals.
- **Conditional future work.** Acquisition requires viability, capital and approval.

## 25. `notifications` (P1)

- **Mandated duty and operator boundary.** Deliver authorized notifications and incident receipts. Staffed receiver is required before the dependent service starts.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Owner-only attention acknowledgments persist as separate receipts. An unconfigured dispatcher leaves delivery unverified. [Primary source](../services/api/app/workers/outbox_dispatcher.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md. Owner attention references are revocable and private; an unconfigured transport cannot produce a delivery receipt. Private acknowledgment was verified for owner-only access, persistent readback, unknown-ID refusal and retry without a duplicate event. Twenty-six restored historical bridge, channel and orchestrator tests run in canonical CI. Explicitly disabled preferences do not create dispatch attempts.
- **Internal next step.** Complete governed external-intent staging, consent and retry workflow. Private acknowledgment is tested. Exercise concurrent outbox replay, opt-out and provider outage.
- **External and independent proof.** Verify independently authorized provider receipt. Provider delivery receipt tied to exact approved intent, endpoint and recipient.
- **Authority and professional review.** Approve sender, recipients, channel and cost. No separate professional item identified.
- **Impact and accountable fallback.** Unverified notifications leave routine work dependent on manual checks. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Technical operator pauses affected dispatch and verifies alert path. Estimated effort 2–4 h.
- **Exact acceptance contract.** Owner-authorized email/SMS external receipts with opt-out, retry, replay protection and consent logs
- **Next action.** Complete governed consent, external-intent staging and retry, then verify an independently authorized delivery receipt.

## 26. `operations_observability` (P0)

- **Mandated duty and operator boundary.** Observe continuity, outages, thresholds and rollback. Duty operator receives and acknowledges escalation.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Owner briefings expose recorded discovery failures and Builder lease health. Private owner attention now surfaces digest-verified current Prime HOLD or blocked receipts and separate integrity references for unverified receipts. An authenticated WeWeb fixture verifies owner-only access, no-cache headers and driving counts without private report details. Continuous external monitoring and notification transport remain open. [Primary source](../services/api/app/heimdall/readiness.py).
- **Current evidence.** Owner integration tests exercise local and driving briefing contracts. Pantheon assignment tests show verified missed cadence records in briefing evidence.
- **Internal next step.** No separately identified coding gap in the matrix. Prove sustained restart, alert continuity and exact repair receipts.
- **External and independent proof.** Commission controlled always-on staging observation. Timestamped actual uptime, alert, restart and recovery receipts.
- **Authority and professional review.** Approve runtime and monitoring scope. No separate professional item identified.
- **Impact and accountable fallback.** No receiving operator means failures can stay unhandled. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Duty operator acknowledges the isolated test event before release. Estimated effort 2–4 h.
- **Exact acceptance contract.** Red/green live status based on DB/worker/provider receipts; alert on stalled jobs, missing routers and invalid migrations
- **Next action.** Verify worker recovery and alerts in a controlled always-on staging run.

## 27. `weweb_frontend` (P1)

- **Mandated duty and operator boundary.** Provide private owner and separately scoped buyer experience. Authorized integrator commissions exact isolated Preview and revocation.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. The private owner routes support JARVIS and attachment access gating. Driving mode includes specialist backlog integrity failures as an attention count. [Primary source](../services/api/app/routers/auth_weweb.py).
- **Current evidence.** Owner API and tenant regressions verify JWT isolation, disposition metadata, restore-hold blocking, no-store and revoked sessions. Private owner startup comparison separates dated public fees, quote and estimate classes, unknowns, activation, reserves and runway. The owner attention and driving briefing datasource is prepared for the authorized preview. Owner Attention is installed in the primary WeWeb Home cockpit (05ce39c3-5a5f-4e26-892b-3aa82fff3051). Editor readback confirms both workflows and volatile variables. Transport fixtures pass owner response, denial, empty state, and exact acknowledgment checks. The primary Home cockpit now has owner-gated local thread creation, history, message submission, exact Prime decision references and attachment metadata. Four installed workflows were read back against tested source. The conversation panel now contains private file selection, SHA-256 upload, and local extraction from exact current ACCEPT_LOCAL metadata. Both document workflows were read back. Fixtures check interrupted upload, approved digest verification, restore hold and refusal outside the authorized origin. The primary Home cockpit has owner-only staging and status for document review and disposal. A separate server mandate binds the matching request digest and current attachment/review state. Read-only Prime/Loki and specialist schedule evidence use the canonical verifier. The six exact editor scripts passed isolated fixture execution, including denial before transport for a subscriber. Hosted run 45050002801 passed all four jobs. Browser and device acceptance are pending. The private startup and draft professional-review panel uses the existing owner-only comparison route. The operating scope panel shows economic decisions, liabilities and segregated statement heads. It refuses non-owner access, altered scope and positive claims of accessible funds. Its comparison and clear workflows were read back, and the exact network action ran against a synthetic revoked-session response. Pantheon role filtering and pagination are available in the owner cockpit.
- **Internal next step.** Bind device-local voice, Legacy mutation controls, broader treasury and household workflows, full domain evidence drill-down and remaining owner/subscriber surfaces. The read-only Legacy operating view exposes economic holds and segregated fixture statements. Document, decision, startup comparison, draft professional review and bounded Pantheon report directory are installed for preview. Exercise revocation, protected state and device outcomes end to end.
- **External and independent proof.** Configure an authorized matching staging API origin and preview CORS. Test owner/subscriber denials, logout and revocation, exact acknowledgment receipt, responsive layout and local voice devices. Observed isolated HTTPS previews with real owner/subscriber separation and device consent.
- **Authority and professional review.** Approve preview access and local speech consent. No separate professional item identified.
- **Impact and accountable fallback.** Local UI proofs leave actual separate-origin account flows open. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Authorized WeWeb integrator holds publication and tests the exact preview. Estimated effort 2–4 h plus entitlement.
- **Exact acceptance contract.** Owner login, real dashboard, approval controls, data updates and session expiry tested in WeWeb against deployment
- **Next action.** Wire the exact owner-preview routes in the December handoff. Verify status handling and device-local speech with a separately authorized preview project and test device.

## 28. `ci_release` (P0)

- **Mandated duty and operator boundary.** Prove reviewed release, regression and rollback. Release operator owns deployment and recovery proof.
- **Stage and source.** `FOCUSED_CI_TESTED`. CI run 44748568129 passed 190 targeted tests including full existing completion-registry suite, 13 critical router and 15 route contracts, original five Gods, private Prime controls, SQLite and PostgreSQL. Broad historical pytest collection still reports two known errors. No production release. [Primary source](../.github/workflows/critical-controls-ci.yml).
- **Current evidence.** See FOCUSED_CI_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** No separately identified coding gap in the matrix. Run reviewed candidate through backup and rollback gates.
- **External and independent proof.** Verify staging build and rollback receipts. Hosted CI, independent staged backup and rollback receipt for exact release candidate.
- **Authority and professional review.** Approve staging release candidate and window. No separate professional item identified.
- **Impact and accountable fallback.** Unverified release and backup leave recovery dependent on improvisation. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Release operator aborts and checks migrated restore before retry. Estimated effort 2–4 h plus elapsed trial.
- **Exact acceptance contract.** Canonical app starts cleanly; all core safety and workflow tests + prod-like Postgres integration; reviewed release/rollback evidence
- **Next action.** Verify staging artifacts, backup and rollback gates on a reviewed release candidate.

## 29. `prime_private_owner` (P0)

- **Mandated duty and operator boundary.** Keep Prime private and accountable to the owner. Technical operator restores access, owner retains authority decisions.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. An opt-in PostgreSQL worker expires owner-reviewed attachment bytes and stored extracts. Restore hold blocks attachment disclosure while a backup is reconciled. [Primary source](../services/api/app/services/attachment_parser.py).
- **Current evidence.** Owner API verifies latest inclusive UTC deadline, restore hold, emergency stop, expiry, idempotent reruns and redacted extracts. Disposable PostgreSQL logical backup rehearsal checked pre- and post-expiry restores. Private owner startup comparison separates dated public fees, quote and estimate classes, unknowns, activation, reserves and runway. Restore tests reconcile an older attachment state under the hold before allowing access checks to resume. An externally pinned disposition manifest closes older snapshots until owner reconciliation, and remains closed on manifest tampering.
- **Internal next step.** Complete remaining scoped attachment-analysis coverage where approved. Bind private registration-based startup review to reconciled financial evidence. Prove restore quarantine, independent disposition receipts and revocation.
- **External and independent proof.** Verify authorized private staging backup recovery and the owner startup independence workflow on WeWeb preview. Independent backup restoration and disposition verification, and independent financial sources when used for startup reliance.
- **Authority and professional review.** Approve retention and test restore scope. No separate professional item identified.
- **Impact and accountable fallback.** An uncommissioned private surface limits practical supervision. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Identity/release operator restores private access and holds changes to authority. Estimated effort 1–3 h.
- **Exact acceptance contract.** Prove no subscriber/clone/tenant can access owner Prime; trace trust and approvals across API, worker, UI, DB and provider adapters.
- **Next action.** Prove staging quarantine and post-snapshot deletion reconciliation with independently retained disposition receipts before clearing the restore hold.

## 30. `pantheon_five_evaluators` (P0)

- **Mandated duty and operator boundary.** Preserve original valuation, sustainability, strategy, risk and ethics evaluators. Hard conflicting decisions hold pending valid evidence.
- **Stage and source.** `FOCUSED_CI_TESTED`. All five original specialist evaluators now call directly from the original governance orchestrator, without recursive TestClient requests. Focused tests verify Tyr hard-stop and advisory-only partial coverage. Expanded continuous cross-system Gods and real dispatch gating remain unproven. [Primary source](../PANTHEON_SUMMARY.md).
- **Current evidence.** See FOCUSED_CI_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Connect independent disagreements through each canonical decision gate. Exercise all five roles with material conflict, refusal and reproducible audit.
- **External and independent proof.** Prove governed dispatch in authorized staging. Scoped work receipts and independently reviewed conflicting advice.
- **Authority and professional review.** Approve scoped worker and reviewer identity. No separate professional item identified.
- **Impact and accountable fallback.** Simple governance checks do not close proactive specialist coverage. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Prime withholds policy-dependent actions when evidence coverage is incomplete. Estimated effort 2–4 h.
- **Exact acceptance contract.** Prove all five independent checks and disagreements reach a real dispatch gate, including legal/ethical hard stops, no forged approvals and reproducible audit.
- **Next action.** Exercise independent outcomes and merge observations through the canonical decision path.

## 31. `pantheon_expanded_bridge` (P0)

- **Mandated duty and operator boundary.** Maintain cross-system independent scoped specialists. Provider/operator supplies authorized inputs, Prime holds uncovered tasks.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Scoped discovery, economic reassessment and outcome publishers feed a durable assignment backlog. Prime's shadow evaluator uses its existing durable queue for independent outcome and exact-scope economic subscriptions. Owners see waiting and integrity failure counts and can page through current assignment receipts by role. The private directory projects only digest-verified matching reports and separately shows exact Loki review state. Prime and governed listing execution recheck the current role and scope of each cited report, and private Prime decision reads revalidate the same references. [Primary source](../services/api/app/routers/foundry_discovery.py).
- **Current evidence.** Approval, contradiction and verified-learning specialists reconcile recent Factory receipts. Forseti, Loki and Tyr can inspect exact checkout fixture evidence. Njord, Forseti, Mimir and Heimdall also inspect scoped business treasury fixture heads. The independent local challenger reports critical contradictions. The integration fixture removed a statement head and verified Njord and independent Loki surfaced the conflict without treating the balance as available cash. Prime holds on scoped contradictions. Pantheon/Prime API regressions exercise scoped queuing, deduplication, replay, stale or missing evidence, digest corruption and emergency stop. Disposable PostgreSQL proves concurrent publishers, recovery from a rolled-back claim, and concurrent economic wakeup deduplication with exact-scope opt-in and rollback. The scoped acquisition fixture verifies debt stress, separately reviewed simulation, receipt reuse, revocation and reevaluation. SaaS, service and real-estate rehearsal covers shared stress rules, projection differences and simulated review. A repeated withdrawal queues one digest-bound event for opted-in Prime schedules and participating specialists. Prime switches to HOLD before cadence and the source is excluded from allocation. Heimdall, Loki, Mimir and Njord can carry an exact scoped economic performance receipt. The local independent challenger reports conflicting net outcome, source identity or evidence basis. Scoped checkout fulfillment holds and unresolved refund support reach Prime reassessment and independent Loki challenge. Norns assignments can observe checkout history without treating fixture activity as commercial outcomes. The owner directory verifies pagination, exact specialist scope, subscriber denial, independent queued review status and missing-receipt holds. The integrated product rehearsal attempts to rebind the existing assignment scope and verifies that both Prime evaluation and private decision readback hold.
- **Internal next step.** Extend domain coverage beyond Factory, checkout, treasury, economic performance and other current evidence lenses. Exercise missing evidence, tenant isolation and end-to-end independent review for each domain.
- **External and independent proof.** Verify separate model and worker behavior in approved staging. Independent domain evidence and scoped specialist worker receipts.
- **Authority and professional review.** Ratify role conflicts and authorize specifically scoped operation. No separate professional item identified.
- **Impact and accountable fallback.** A shared local lens is insufficient for independent cross-system findings. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Prime requests role-specific evidence and holds dependent actions. Estimated effort 2–4 h.
- **Exact acceptance contract.** Map historical role/authority variants without losing user intent; test controlled bridge and no unrestricted agent-to-agent tools; owner ratifies conflicting labels. Owner-confirmed 2026-11-20: prove every specialist covers all authorized relevant subsystems via scheduled and event-driven analysis, durable scoped reports to Prime, independent Loki cross-system challenges, and Prime synthesis/decision/verified execution inside existing mandates without routine owner approval; test missing/stale evidence, escalation and tenant isolation.
- **Next action.** Extend substantive domain coverage and explicit contradiction handling. Prove independent Loki review of scoped evidence continuing to a governed Prime decision, verified execution and Mimir reassessment.

## 32. `norns_probability_calibration` (P1)

- **Mandated duty and operator boundary.** Calibrate Norns on prospective observed outcomes. Statistician or authorized reviewer validates calibration and drift.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Prospective holdout enrolment persists before resolution or deadline. Holdouts stay outside baseline training and ordinary calibration. Evaluation separates holdouts and ordinary observations by estimate source. [Primary source](../services/api/app/pantheon/forecasts.py).
- **Current evidence.** See SQLITE_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md. Product Foundry continuous fixture links signed discovery, independent challenge, scoped execution, outcome, retained losses and a subsequent HOLD with contradiction evidence. Calibration and prospective training verify original Factory proof. Scoped Norns reports use the assignment horizon. The private API offers an exact horizon filter, predicted versus observed frequency buckets, and rejection of late holdout enrollment. Existing scoped Norns ticks resolve eligible Factory outcomes in a bounded scan. PostgreSQL demonstrates lock deferral, rollback recovery and scope isolation.
- **Internal next step.** No separately identified coding gap in the matrix. Replay out-of-order outcomes and sustained recovery using fixtures; prove fixture outcomes never calibrate the observed result.
- **External and independent proof.** Commission scoped Norns worker and controlled outcome stream. Genuine independently observed and dated outcomes with calibration denominators.
- **Authority and professional review.** Approve worker and outcome data scope. No separate professional item identified.
- **Impact and accountable fallback.** No prospective mature observations means weak calibration. Blocks the first business if the selected model, interface or escalation needs it. Defer unused branches and keep them disabled. Norns labels uncertainty and defers confidence claims. Estimated effort 2–4 h plus actual observation interval.
- **Exact acceptance contract.** Quantify calibration and regret on holdout real outcomes; stop claiming precise first-revenue odds from synthetic scores.
- **Next action.** Verify sustained worker operation in authorized staging and collect eligible observed outcomes beyond the internal fixture.

## 33. `owner_commander_voice` (P1)

- **Mandated duty and operator boundary.** Explain choices and capture owner dispositions and intervention. Private supervised profile holds unsupported commands.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Read-only driving playback and parked device-local dictation have simulated-browser coverage. A transcript is an editable draft. [Primary source](../docs/UNIVERSAL_OPPORTUNITY_PIPELINE.md).
- **Current evidence.** test_saas_tenant_entitlements.py verifies the authenticated read-only driving briefing, including the emergency-stop state. Verified missed cadence counts are included in its attention summary. Local browser selection tests enforce consent, device-local speech and text fallback. Simulated dictation covers preinstalled local processing, consent, text-only fallback and cancellation.
- **Internal next step.** Bind parked dictation and finish owner decision-option interactions in the preview. Rehearse permission denial, fallback and simulated microphone revocation.
- **External and independent proof.** Verify approved physical devices and preview app. Owner-approved physical device results for fallback, playback and microphone revocation.
- **Authority and professional review.** Approve test device and grant per-session microphone consent. No separate professional item identified.
- **Impact and accountable fallback.** Unverified voice or motion paths threaten owner authority and accessibility. Blocks the first business if the selected model, interface or escalation needs it. Defer unused branches and keep them disabled. Use the authenticated private interface and hold sensitive voice commands. Estimated effort 1–3 h.
- **Exact acceptance contract.** Prove authentic owner briefing, dissent, Norns odds, A/B/C/Override with recorded decisions, secure voice/mobile controls and fallback behavior.
- **Next action.** Bind parked dictation and decision-option review in the owner preview, then verify on approved devices.

## 34. `five_initial_legacies` (P0)

- **Mandated duty and operator boundary.** Prepare five separately governed Legacy scopes. Owner approves each mandate, separate delegates operate them.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Legacy registry and internal work path exist; five independent profitable operations unproven. [Primary source](../services/api/app/models/completion_registry.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Complete remaining mandate-specific onboarding and proof paths. Demonstrate five separate scopes, worker receipts and economics.
- **External and independent proof.** Commission each approved Legacy independently. Five distinct approved operating scopes and independent execution and economic receipts.
- **Authority and professional review.** Select five startup mandates and legal authority. Qualified review only for a selected mandate involving regulated or otherwise review-dependent activity.
- **Impact and accountable fallback.** Five data partitions alone do not create operating businesses. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Prime holds each tenant lacking a signed lane, material rights and support capacity. Estimated effort 1–3 h per selected scope.
- **Exact acceptance contract.** Prove five owner-selected mandates with tenant isolation, durable worker, lawful external acts, separately reconciled revenue and cash controls.
- **Next action.** Prove each planned startup Legacy can operate under its own scope and reconciled economics.
- **Conditional future work.** Expansion follows viable units.

## 35. `clones_vs_mirrors` (P1)

- **Mandated duty and operator boundary.** Clone proven playbooks and mirror regional operating scopes. Authorized regional and technical operators verify rights and isolation.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Owner-authorized registry rehearsal creates distinct business clone and regional mirror receipts, separate namespaces and inactive target rows. Staged runtime separation and live scaling remain open. [Primary source](../docs/VALHALLA_DOCTRINE_CONFLICT_MAP.md).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Close uncovered capability and isolation gaps in the existing rehearsal. Rehearse clone and regional-mirror replay, isolation and restore in disposable local runtimes.
- **External and independent proof.** Commission staged runtimes with shared governance. Separate host and regional execution, isolation and restore receipts.
- **Authority and professional review.** Approve selected territories and processing scopes. No separate professional item identified.
- **Impact and accountable fallback.** Incorrect replication can copy authority, data or risk. Defer for the first bounded commerce lane. Blocks autonomous operation of this domain when selected. Integrator holds clone/mirror activation and checks regional licences and boundaries. Estimated effort 3–6 h per approved expansion.
- **Exact acceptance contract.** Verify no mirror has external authority; governed clone lifecycle, real business identity, permissions, budget and data separation.
- **Next action.** Test clones and mirrors with staged independent runtimes and shared governance.
- **Conditional future work.** Replication follows proven playbooks.

## 36. `product_foundry_subscriptions` (P1)

- **Mandated duty and operator boundary.** Sell scoped subordinate products while keeping Prime private. Product and subscription delegates handle support and release.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. The verified internal listing reaches signed local checkout, delivery, attribution and refunds. Trial module entitlements are tenant-bound. Storefront, paid licenses, settlement and renewal are pending. [Primary source](../services/api/app/routers/foundry_checkout.py).
- **Current evidence.** See SQLITE_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md. Product Foundry continuous fixture links signed discovery, independent challenge, scoped execution, outcome, retained losses and a subsequent HOLD with contradiction evidence.
- **Internal next step.** Complete supported entitlement and repeatable delivery flows. Prove refunds, support and multi-tenant fulfillment continuity.
- **External and independent proof.** Commission approved storefront and subscription sandbox. Authorized provider payment, participant receipt and support/revocation events.
- **Authority and professional review.** Approve rights, product, merchant scope and launch gates. No separate professional item identified.
- **Impact and accountable fallback.** A private Prime capability may be exposed as a customer product. Blocks the first business if the selected model, interface or escalation needs it. Defer unused branches and keep them disabled. Product operator isolates the specific entitlement and holds commercial access if separation fails. Estimated effort 3–6 h.
- **Exact acceptance contract.** Complete approved subordinate product package, storefront, real checkout/provider receipt, delivery, refund/chargeback, ledger and customer subscription lifecycle.
- **Next action.** Complete the authorized storefront, entitlements, refunds and repeatable fulfillment path.
- **Conditional future work.** Scale from viable subscription economics.

## 37. `independent_venture_foundry` (P1)

- **Mandated duty and operator boundary.** Discover, build and operate authorized cross-industry ventures. Prime runs routine work after corroborated evidence, sector delegate covers exceptions.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. A source-backed unfamiliar business can reach scoped Pantheon analysis, Universal Evaluator shadow recommendation, comparative capital ranking and independent review. Commercial operation and measured demand remain pending. [Primary source](../services/api/app/routers/foundry_discovery.py).
- **Current evidence.** See SQLITE_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md. The scoped acquisition fixture verifies debt stress, separately reviewed simulation, receipt reuse, revocation and reevaluation. SaaS, service and real-estate rehearsal covers shared stress rules, projection differences and simulated review. A repeated withdrawal queues one digest-bound event for opted-in Prime schedules and participating specialists. Prime switches to HOLD before cadence and the source is excluded from allocation.
- **Internal next step.** Extend independently sourced demand selection and governed pilot preparation. Exercise authority-bound pilot and contradictory demand evidence.
- **External and independent proof.** Stage approved proof for one selected candidate. Independent demand, cost and scope-bound pilot outcomes.
- **Authority and professional review.** Approve pilot, source rights and scope. No separate professional item identified.
- **Impact and accountable fallback.** Without independent evidence, the Foundry can choose a convenient fixture. Blocks the first business if the selected model, interface or escalation needs it. Defer unused branches and keep them disabled. Prime records uncertainty, seeks real inputs and abstains pending independent challenge. Estimated effort 2–4 h plus research window.
- **Exact acceptance contract.** Scheduled discovery and evidence validation, owner-bounded creation of a new lawful venture, live sales and repeatable outcome learning.
- **Next action.** Prove independently sourced demand and exercise one authority-bound startup candidate.
- **Conditional future work.** Expand only when a better justified opportunity appears.

## 38. `real_estate_portfolio_legs` (P1)

- **Mandated duty and operator boundary.** Operate approved property portfolio lanes under verified controls. Broker, property manager, lawyer or field service where applicable.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Real estate strategy models cover wholesaling, flipping, hold and related categories; external closings unverified. [Primary source](../docs/MILLION_PATH_STRATEGY_LAYER.md).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md. SaaS, service and real-estate rehearsal covers shared stress rules, projection differences and simulated review. A repeated withdrawal queues one digest-bound event for opted-in Prime schedules and participating specialists. Prime switches to HOLD before cadence and the source is excluded from allocation.
- **Internal next step.** Complete remaining distinct portfolio-branch rehearsals. Exercise stale comparable, inconsistent cost and recovery evidence using fixtures.
- **External and independent proof.** Stage authorized data and practice transaction. Independent current comparable, recovery and costs in each selected jurisdiction.
- **Authority and professional review.** Select target jurisdiction and qualified reviewers. Qualified property, legal and accounting review as applicable before acquisition.
- **Impact and accountable fallback.** A property plan without field execution and independent numbers is speculative. Defer for the first bounded commerce lane. Blocks autonomous operation of this domain when selected. Delegate field work to licensed and contracted providers while holding commitments. Estimated effort 4–8 h coordination plus quotes.
- **Exact acceptance contract.** Real licensed/legal deal source→underwriting→buyer→contract→closing→settlement with real receipts; replay and privacy controls.
- **Next action.** Complete remaining portfolio rehearsals with grounded jurisdiction and comparable evidence.
- **Conditional future work.** Asset purchases depend on capital and viability.

## 39. `treasury_banking_controls` (P0)

- **Mandated duty and operator boundary.** Protect liabilities, operating reserves and verified cash. Treasury operator and accountant resolve mismatches, owner authorizes funds movement.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Statement fixtures reconcile segregated balances and unique transaction references. A signed checkout delta can be matched once to an exact business statement fixture. Historical quarantined FX records and actual bank verification remain separate. [Primary source](../services/api/tests/test_floor_currency.py).
- **Current evidence.** test_economic_control.py covers segregated fixture statements and historical vault flags. Product artifact rehearsal adds fixture settlement. Private owner startup comparison separates dated public fees, quote and estimate classes, unknowns, activation, reserves and runway.
- **Internal next step.** Exact same-scope recurring bank booking and separately gated Plaid CAD balance observation have implementation. A bounded CAD cash close joins independent bank observations, balanced journal and distinct enrolled accounting evidence to the existing allocation preview. Completed subscriber-acknowledged recurring service can release exact settled liabilities for a single open accounting period. Complete cross-period recurring recognition, unsupported corrections and broader business-scope cash evidence. The scoped owner dashboard exposes bank match, acknowledged service, liability release and held counts. Rehearsals, holds and incomplete evidence cannot supply recognized income or cash. Exercise reversal, restrictive reserve and double-counted obligation scenarios in isolated accounting fixtures.
- **External and independent proof.** Commission approved bank readback and exact QuickBooks sandbox account metadata. Verify financial evidence, approved funding feeds and posting authority separately. Exact independently issued bank and accounting records, reconciled liabilities, reserve evidence and reversals.
- **Authority and professional review.** Approve read-only scope and professional integration. Qualified banking and accounting review of classified funds and actual posting scope.
- **Impact and accountable fallback.** Missing bank and reserves evidence can overstate available funds. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Treasury operator and accountant hold movement and verify both sides of the match. Estimated effort 2–5 h.
- **Exact acceptance contract.** Prove every actual transfer requires owner intent, cap, whitelisted accounts, durable idempotency and a bank settlement receipt; no fake success.
- **Next action.** Match independently supplied statements and liabilities with payment and accounting sandbox evidence.
- **Conditional future work.** Actual allocations depend on reconciled funds. The reverse commercial target and private independence linkage use scoped reconciliation fixtures until an actual-provider evidence path is accepted.

## 40. `infinite_banking_insurance` (P1)

- **Mandated duty and operator boundary.** Evaluate participating insurance and financing effects. Licensed insurance adviser validates an actual illustration and terms.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Whole-life policy records exist, not a real participating-policy premium/cash-value loan model; no insurer/bank transfer proof. [Primary source](../services/api/app/models/whole_life_policy.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Prepare the existing source-backed scenario and compare alternatives. Rehearse assumptions, fee omissions and sensitivity using clearly synthetic illustrations.
- **External and independent proof.** Obtain independently supplied policy illustrations. Carrier illustrations and terms with current effective dates.
- **Authority and professional review.** Approve whether to request an illustration or later pursue a reviewed policy. Licensed insurance professional reviews suitability, costs and terms.
- **Impact and accountable fallback.** Insurance projections cannot establish legal coverage or affordability. Defer for the first bounded commerce lane. Blocks autonomous operation of this domain when selected. Use a licensed insurance adviser and hold applications or premium commitments. Estimated effort 2–4 h professional time plus quote.
- **Exact acceptance contract.** Model actual policy illustration, fees, premiums, loan balance and interest, tax/legal/contract details, adverse scenarios; owner and licensed review before any loan.
- **Next action.** Build a sourced scenario and obtain the required insurance and professional review.
- **Conditional future work.** Funding depends on viability and available capital.

## 41. `estate_and_master_trusts` (P1)

- **Mandated duty and operator boundary.** Model lawful trust and succession structures privately. Qualified trust counsel and trustees handle formation and decisions.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Legal trust concepts and entity records are present, not actual trust formation. Historic Panama-first vs Canadian-first source conflict unresolved. [Primary source](../services/api/app/models/trust.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Prepare comparative fact packet and jurisdiction requirements. Verify contradictory fact sources and reliance holds with synthetic opinions.
- **External and independent proof.** Verify approved document workflow using fixtures. Official title/entity documents and dated signed scoped opinions.
- **Authority and professional review.** Select the objectives and approve any proposed trust action separately. Licensed counsel validates the selected trust before reliance.
- **Impact and accountable fallback.** A source document cannot establish a valid trust. Defer for the first bounded commerce lane. Blocks autonomous operation of this domain when selected. Trust counsel handles jurisdiction/authority and holds restructuring. Estimated effort 2–5 h consultation estimate.
- **Exact acceptance contract.** Trace trustee, protector, beneficiaries, assets and succession; compare structures under cross-border professional advice and preserve owner-approved choice. No auto filings.
- **Next action.** Prepare competing trust options with lawful jurisdiction-specific professional reviews.
- **Conditional future work.** Asset transfer and settlement require separate authorization and viable funding.

## 42. `canada_exit_strategy` (P1)

- **Mandated duty and operator boundary.** Evaluate Canadian departure and residence scenarios. Qualified tax and immigration practitioners review before action.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. International residency and departure concepts are advisory documents; legal/tax outcomes and exact timing unverified. [Primary source](../legal/TRUST_RESIDENCY_OVERVIEW.md).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md. Private owner startup comparison separates dated public fees, quote and estimate classes, unknowns, activation, reserves and runway.
- **Internal next step.** Build scoped timing, residency and obligations evidence packet. Test conflicting residence and obligation assumptions with independent evidence.
- **External and independent proof.** Obtain authorized official records if required. Current official records and substantiated residence and reporting evidence.
- **Authority and professional review.** Select departure timing only after reviewing applicable duties. Qualified cross-border tax and legal review before departure or filing reliance.
- **Impact and accountable fallback.** A departure estimate cannot establish legal or tax residency. Defer for the first bounded commerce lane. Blocks autonomous operation of this domain when selected. Tax and immigration advisers hold exit steps until written review. Estimated effort 2–5 h consultation estimate.
- **Exact acceptance contract.** Produce evidence-backed Canada personal/corporate departure scenarios, tax residence tests, continuing ties, immigration, family requirements, legal opinions and actionable owner choices.
- **Next action.** Prepare evidence and professional questions on departure timing and obligations.
- **Conditional future work.** Execution is conditional on personal and business readiness.

## 43. `global_residency_options` (P1)

- **Mandated duty and operator boundary.** Evaluate authorized international residency and business options. Local qualified specialists confirm facts and eligibility.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Panama/Bahamas and future jurisdictions appear in models/plans. No immigration status or lawful tax residency independently proven. [Primary source](../services/api/app/models/bahamas_plan.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Structure jurisdiction and eligibility evidence for requested options. Exercise expired evidence and incomplete eligibility packets with fixtures.
- **External and independent proof.** Collect authorized records and validate applicable official processes. Official requirements and actual owner eligibility documents for the selected option.
- **Authority and professional review.** Choose the jurisdictions to evaluate and approve document access. Qualified immigration or tax adviser verifies eligibility and implications when the option is pursued.
- **Impact and accountable fallback.** Unverified eligibility leaves residency, tax and timing uncertain. Defer for the first bounded commerce lane. Blocks autonomous operation of this domain when selected. Immigration specialist verifies eligibility and pauses any filings. Estimated effort 2–5 h consultation estimate.
- **Exact acceptance contract.** Compare owner-approved country options, rights, real costs, residency/tax reporting and professional validation with no invented approval status.
- **Next action.** Collect official jurisdiction requirements and independent eligibility review when requested.
- **Conditional future work.** Pursue options when mobility plan and financing justify them.

## 44. `tax_opinions_legal` (P0)

- **Mandated duty and operator boundary.** Record sourced legal and tax requirements and opinion version. Qualified adviser validates conclusions and filings.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. The private startup planner prepares jurisdiction-specific review packets. The signed opinion intake and separate scoped reliance approvals verify exact evidence, independent enrolled qualified review, owner authorization, revocation, expiry and emergency stop. [Primary source](../services/api/app/models/tax_interpretations.py).
- **Current evidence.** The startup workflow produces private dated fact-and-question packets. Local signed-opinion tests verify owner auth, signer scope, byte hash, owner document review, invalidated keys, attachment deletion and exact replay. The rehearsal validates the qualified review signature, disallows the original signer, rejects altered or mismatched scope, rechecks key withdrawal and emergency state, and demonstrates idempotent owner revocation.
- **Internal next step.** No separately identified coding gap in the matrix. Repeat synthetic wrong-party, expiry, revocation and cross-scope reliance cases for any newly provided decision template.
- **External and independent proof.** Independently verify the author and reviewer qualifications, enroll distinct scoped public keys and commission a private signed file and reviewed reliance grant. Verification of independent author and reviewer qualifications, signed opinion and scope.
- **Authority and professional review.** Approve the exact internal decision scope and retain the ability to revoke reliance. Qualified independent professionals author and review the exact scoped opinion.
- **Impact and accountable fallback.** Unknown obligations can prevent selling lawfully. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Lawyer or accountant records applicable written advice and holds the affected sale or filing. Estimated effort 1–5 h initial professional time.
- **Exact acceptance contract.** Require source, date, jurisdiction, legal signoff and preserved opinion files; prohibit AI-led filing, fraud, tax evasion and unsupported tax treatments.
- **Next action.** Commission the private opinion and reliance workflow with independently qualified professionals.

## 45. `reinvestment_funfund_policy` (P1)

- **Mandated duty and operator boundary.** Recommend allocation and reserve protection under current mandate. Owner sets policy and accountant verifies classifications.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. The dynamic policy is the current recommendation model. It reconciles monthly CAD checkout-linked performance and a scoped statement fixture, applies owner-configured anchors and protections, and produces a private review receipt. The former 90/10 and first-year deferred model remains a historical scenario contract. [Primary source](../valhalla_hand_off/ACCOUNTING_PACKAGE/01_fund_separation.md).
- **Current evidence.** See SQLITE_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Link reviewed allocations to exact reconciled cash and obligations. Rehearse conflicting reserves, payroll, caps and withdrawal denials with fixtures.
- **External and independent proof.** Exercise approved treasury and accounting sandbox. Independently reconciled cash, taxes, payroll, reserves and licensed accounting evidence as applicable.
- **Authority and professional review.** Approve policy parameters and real withdrawal authority. Qualified accounting review for payout, payroll and tax basis as applicable.
- **Impact and accountable fallback.** Unverified allocation or personal cash exposes restricted funds. Blocks the first business if the selected model, interface or escalation needs it. Defer unused branches and keep them disabled. Treasury operator keeps funds held and asks for mandate approval only as required. Estimated effort 2–5 h.
- **Exact acceptance contract.** Verify owner-private cap schedule, taxes, cash reserves, net profit definition, allocation ledger, no unauthorized extraction and documented exceptions.
- **Next action.** Link reviewed allocation policy to separately reconciled compensation, reserves and withdrawals.
- **Conditional future work.** Withdrawals depend on reconciled funds and applicable policy.

## 46. `family_payroll_succession` (P2)

- **Mandated duty and operator boundary.** Support genuine lawful family employment and succession. Payroll provider, counsel and authorized successor handle actual duties.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Archived family payroll source exists; not current operational payroll evidence. [Primary source](../_archive/legacy_pre_canonicalization/backend_system/app/core_gov/family_payroll/store.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Complete scoped role and succession documentation flows. Test authority, payroll and handover evidence.
- **External and independent proof.** Verify approved payroll workflow if commissioned. Role, payroll and authority handover records when implemented.
- **Authority and professional review.** Confirm roles and approve the exact scoped payroll or succession changes. Qualified payroll and succession advisers review the applicable records and authority.
- **Impact and accountable fallback.** Payroll, employment and succession bring specialized legal duties. Defer for the first bounded commerce lane. Blocks autonomous operation of this domain when selected. Payroll provider or counsel handles applicable acts and holds onboarding/payroll while unverified. Estimated effort 2–5 h plus vendor quote.
- **Exact acceptance contract.** Keep private lawful employment/payroll/succession only with genuine service, privacy, remuneration evidence, professional filings and owner signoff.
- **Next action.** Confirm roles, purpose, documentation and professional payroll review.
- **Conditional future work.** Hiring and payouts depend on sustainable operating funds.

## 47. `bahamas_resort_growth` (P2)

- **Mandated duty and operator boundary.** Evaluate and eventually operate approved resort scope. Local permits, hospitality operator and qualified professionals.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Resort/vault models exist; live property control, bookings and income have no independently verified receipts. [Primary source](../services/api/app/models/bahamas_vault.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** No separately identified coding gap in the matrix.
- **External and independent proof.** No separate provider item identified. Independent property, financing, diligence and cash-flow evidence when justified.
- **Authority and professional review.** Select and approve a viable acquisition only after evidence and advice. Qualified property, local legal, banking and tax review before acquisition.
- **Impact and accountable fallback.** Resort planning cannot guarantee licences, staffing or capital. Defer for the first bounded commerce lane. Blocks autonomous operation of this domain when selected. Local licensed, operations and hospitality partners perform diligence while expansion is held. Estimated effort 4–8 h initial coordination plus quotes.
- **Exact acceptance contract.** Legal ownership, hospitality licensing, bookings, operations, receipts, tax rules and owner-approved capital gates.
- **Next action.** Defer property and hospitality execution pending evidence-backed viability and owner approval.
- **Conditional future work.** Property and hospitality work depends on viability, sufficient capital and professional approval.

## 48. `shield_blackice_protection` (P1)

- **Mandated duty and operator boundary.** Monitor and contain risks across Shield and Black Ice. Independent authorized duty operator handles emergencies and safe recovery.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Black Ice/Shield models and code exist; later doctrine explicitly requires gated validation. [Primary source](../services/api/app/models/protection_stack.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Extend defensive safeguards for the remaining scoped failures. Rehearse restoration, containment and locked access with durable proof.
- **External and independent proof.** Commission a controlled recovery exercise. Observed scoped incident, containment and restore receipt.
- **Authority and professional review.** Approve environment, incident authority and recovery boundaries. No separate professional item identified.
- **Impact and accountable fallback.** Missing continuity operators could delay containment or restore. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Duty operator paged, automated stop persists and restore stays isolated. Estimated effort 2–5 h plus trial time.
- **Exact acceptance contract.** Prove operational fail-safe, exception alerts, containment, no unauthorized surveillance, legal boundaries and rollback during real faults.
- **Next action.** Rehearse threat-specific protection and emergency recovery in controlled operating scope.

## 49. `recruitment_and_va` (P2)

- **Mandated duty and operator boundary.** Recruit and route qualified delegates using approved human oversight. Recruitment and privacy representatives handle actual staffing.
- **Stage and source.** `SOURCE_INSPECTED_ONLY`. Professional alignment code exists; historical employee/cognitive tasks not certified as valid assessment. [Primary source](../services/api/app/routers/pro_alignment_engine.py).
- **Current evidence.** See SOURCE_INSPECTED_ONLY and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Build scoped delegation acceptance and privacy checks. Verify human review, revocation and least-privilege work access.
- **External and independent proof.** Exercise approved personnel workflow where selected. Approved agreement, delegated access and observed revocation receipt.
- **Authority and professional review.** Approve hiring and role scope before delegating access. No separate professional item identified.
- **Impact and accountable fallback.** Absence of staffing prevents lawful or physical exception delivery. Blocks the first business if the selected model, interface or escalation needs it. Defer unused branches and keep them disabled. Independent representative or specialist handles approved tasks, otherwise affected work holds. Estimated effort 2–5 h setup plus operator quote.
- **Exact acceptance contract.** Use job-related exercises, structured interviews, privacy, equal access and accountable owner hiring review; no presumed personality prediction.
- **Next action.** Build scoped delegation acceptance and privacy checks with human hiring review.
- **Conditional future work.** Hiring follows operating workload and capital.

## 50. `loki_independent_challenger` (P0)

- **Mandated duty and operator boundary.** Preserve independent Loki dissent and re-review material changes. Separately controlled reviewer and material exception owner only when needed.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Independent Loki receipts and reconsideration remain required for reviewed specialist material. Staging advice excludes the active Prime model across providers. Findings and decision clearance require a digest-bound completed independent receipt. Legacy unbound history remains readable. The analyst worker recomputes the canonical result digest from its submitted findings and the API-assigned finding IDs. It also verifies the review, artifact, analysis reference and configured reviewer identity. Run-stamped UTC logs expose the receipt digests for staging comparison. A separate staged model, reviewer process and transport proof remain pending. [Primary source](../services/api/app/routers/provider_evidence.py).
- **Current evidence.** See SQLITE_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md. Product Foundry continuous fixture links signed discovery, independent challenge, scoped execution, outcome, retained losses and a subsequent HOLD with contradiction evidence. The scoped acquisition fixture verifies debt stress, separately reviewed simulation, receipt reuse, revocation and reevaluation. Local independent analysis returns a critical contradiction when a Pantheon report's economic result differs from its cited performance fixture. Verified held fulfillment and open refund support are independently flagged as critical operating findings before material reliance. Regression exercises mutated findings, unbound historical receipts and reviewer credential collisions while preserving the raw history. The local analyst records material objections to malformed market evidence, unbound economic performance claims and fixture treasury reports that claim accessible funds. The checks reconcile artifact claims and do not establish source truth.
- **Internal next step.** Extend domain-specific contradiction checks with provenance beyond current evidence lenses. Exercise exact artifact review and disagreement isolation for new domains.
- **External and independent proof.** Validate distinct credentials and approved staged model challenges. Distinct credentials, input digest, independent challenge and material conflict disposition.
- **Authority and professional review.** Approve model scope, independent identity and data class. No separate professional item identified.
- **Impact and accountable fallback.** No genuine separate challenge means unsupported execution risk. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Separately controlled reviewer checks exact digest and Prime holds on stale or absent result. Estimated effort 2–4 h plus reviewer quote.
- **Exact acceptance contract.** Independently audit immutable Heimdall proposals with contrary evidence and sourced objection ledger, prove re-audit after changes, equal-standing owner dissent, lawful professional escalation, and mandatory fail-closed high-risk dispatch; realistic adversarial cases and reviewer outage tested in Postgres/staging. Prove proactive cross-system coverage, reports to Prime, immutable independent dissent and recorded Prime response. Owner receives exceptions rather than approving every routine decision.
- **Next action.** Validate separate model credentials and review exact owner-authorized staged challenges.

## 51. `investment_and_trading_intelligence` (P1)

- **Mandated duty and operator boundary.** Evaluate investments with documented data/model limits. Licensed adviser or broker handles regulated activities under separate mandate.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Owner-private licensed-practice intake records scoped stock, ETF, bond and macro batches. Decimal paper replay includes execution costs, benchmark comparisons, drawdown and concentration. Scoped Pantheon reports, independent Loki review, separately sourced Norns samples and Mimir paper receipt recall are exercised with fixtures. Provider truth and actual investment results remain unverified. [Primary source](../services/api/app/routers/market_intelligence.py).
- **Current evidence.** See SQLITE_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Extend advisory outcome and exposure evidence beyond current replay. Exercise simulated calibration and exclusion of unsupported securities.
- **External and independent proof.** Verify licensed market sources read-only. Licensed historical and independently observed advisory outcome evidence.
- **Authority and professional review.** Approve data rights and advisor scope. Qualified review when regulated activity or actual reliance is proposed.
- **Impact and accountable fallback.** Paper investment results cannot verify advisor authority or live performance. Defer for the first bounded commerce lane. Blocks autonomous operation of this domain when selected. Licensed specialist reviews evidence and keeps transactions disabled. Estimated effort 2–4 h consultation estimate.
- **Exact acceptance contract.** Prove authorized, provenance-bound stock, ETF, bond, dividend, policy and capital-flow research, portfolio risk, no-lookahead historical replay with realistic costs and benchmark comparison, durable paper accounting, independent Loki challenge, prospective Norns calibration and Mimir outcome lineage, owner alerts and advisor-only governance.
- **Next action.** Source licensed market evidence and independently measure advisory outcomes.
- **Conditional future work.** Transactions or increased exposure require separate authority.

## 52. `currency_arbitrage_and_fx_intelligence` (P1)

- **Mandated duty and operator boundary.** Evaluate FX and arbitrage with real fees, fills and controls. Authorized treasury and regulated counterparties handle approved funds actions.
- **Stage and source.** `SQLITE_INTEGRATION_TESTED`. Bounded Decimal quote replay compares direct conversion, cross-venue loops and triangles under bid, ask, freshness, depth, fees and cumulative settlement constraints. Partial and failed fills retain residual currency positions and do not write revenue or treasury. The old FX metrics job now computes virtual equity separately from the treasury vault. [Primary source](../services/api/app/arbitrage/service.py).
- **Current evidence.** See SQLITE_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md.
- **Internal next step.** Extend settlement delay and reconciliation coverage for approved venues. Exercise paper replay with stale quotes, fees, delayed settlement and provider mismatch.
- **External and independent proof.** Verify read-only licensed quotes, venue delays and real reconciliation evidence. Independent time-stamped venue quotes, account terms and reconciliation outcomes.
- **Authority and professional review.** Approve provider access and data terms. Qualified review before any regulated, transfer or live funds authority is proposed.
- **Impact and accountable fallback.** Simulated FX advantage can obscure fees, slippage or regulated activity. Defer for the first bounded commerce lane. Blocks autonomous operation of this domain when selected. Treasury and qualified provider hold trading and verify costs on approved paper data. Estimated effort 2–4 h consultation estimate.
- **Exact acceptance contract.** Prove source-entitled timestamped bid and ask inputs, independent quote and liquidity validation, deterministic cross-venue and triangular replay with costs and settlement risk, partial and failed fills reconciled by currency, exposure limits, emergency stop and regional scope isolation. Treasury recommendations remain advisor-only with no leverage, external orders or transfers.
- **Next action.** Verify licensed quotes, venue delays, reconciliation and FX advisory calibration.
- **Conditional future work.** Live FX, transfers and risk increases require separate authority.

## 53. `dynamic_capital_allocation_loss_containment_and_strategic_redeployment` (P0)

- **Mandated duty and operator boundary.** Reassess and redeploy capital while preserving downside limits. Treasury delegate reconciles evidence and holds material changes for authorization.
- **Stage and source.** `POSTGRES_INTEGRATION_TESTED`. Adds reviewed restart with fresh evidence, scoped obligations, one-use reservation release, per-currency portfolio exposure, and asset recovery linked to fixture statements. PostgreSQL verifies a racing release settles once. Factory queue admission, execution, new per-action approval, standing draft mandates and rehearsal fulfillment re-check known related mirror containment. Fresh Legacy queue admission checks containment, and failover checks both the failed and recovery scopes before moving work. Reading queued state and revoking authority remain available after a hold. An opted-in Prime schedule moves to advisory HOLD immediately after a fixture loss breaches its cumulative ceiling. [Primary source](../services/api/app/services/stripe_bank_booking.py).
- **Current evidence.** See POSTGRES_INTEGRATION_TESTED and source observations above, with exact releases in ops/CHANGE_LEDGER.md. Product Foundry continuous fixture links signed discovery, independent challenge, scoped execution, outcome, retained losses and a subsequent HOLD with contradiction evidence. The scoped acquisition fixture verifies debt stress, separately reviewed simulation, receipt reuse, revocation and reevaluation. SaaS, service and real-estate rehearsal covers shared stress rules, projection differences and simulated review. A repeated withdrawal queues one digest-bound event for opted-in Prime schedules and participating specialists. Prime switches to HOLD before cadence and the source is excluded from allocation. The disposable rehearsal kept both currency pools at zero after a cross-scope hold, retained the separate accounting history and preserved the ability to record a liability.
- **Internal next step.** Apply the containment proof to remaining adapters and non-fixture capital evidence. Existing funding and dispatch gates now span all registered scopes for the same business ID. Exercise staggered loss, restart and reserve evidence across lanes.
- **External and independent proof.** Reconcile independently supplied liabilities and reserves in approved staging. Independently reconciled actual cash, restricted funds, liabilities and operating reserves.
- **Authority and professional review.** Approve scoped funding, review obligations and any release. Qualified accounting or banking review of actual reserve, liability and distribution treatment as applicable.
- **Impact and accountable fallback.** Missing realized economics or stop state can over-allocate capital. Blocks applicable first-business scope and broader autonomy. Defer breadth outside that scope. Prime freezes redeployment, then obtains independent finance evidence and the authorized disposition. Estimated effort 2–5 h.
- **Exact acceptance contract.** Prove independent evidence and hard cumulative limits, protected reserves and aggregate exposure, version and replay integrity, scheduled and event-driven reassessment, exact Loki review, immediate containment, scope isolation, forward alternative ranking, strategic exit with rights-aware asset inventory, and Mimir learning that distinguishes simulation, zero external effects and independently reconciled outcomes.
- **Next action.** Extend containment to every authorized execution lane and reconcile independently supplied reserves and liabilities.
- **Conditional future work.** Expansion follows demonstrated economics and capital availability.
