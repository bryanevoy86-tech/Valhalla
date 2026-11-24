# UNIVERSAL VALHALLA OPPORTUNITY PIPELINE (PHASE THREE)

## Objective

Build and certify a universal cross-engine opportunity pipeline that:

- evaluates opportunities across multiple engines using normalized dimensions
- applies engine-specialist analysis before ranking
- routes every candidate through universal Pantheon governance
- preserves Loki and Norns outputs as structured evidence
- reuses owner approval envelope behavior from certified stack
- supports abstention when no candidate meets deployment threshold
- enforces shadow safety counters with zero external side effects

Constraint honored:

- The certified real-estate Pantheon stack was not redesigned.
- Phase Three extends behavior in the completion registry layer while preserving Phase Two flow.

## Canonical Implementation

- Router: services/api/app/routers/completion_registry.py
- Test suite: services/api/tests/test_completion_registry.py
- Certification artifact: docs/_phase3_universal_opportunity_certification.json

## Endpoints Added

1. GET /api/completion/phase3/universal-opportunity/engine-audit
2. POST /api/completion/phase3/universal-opportunity/evaluate
3. POST /api/completion/phase3/universal-opportunity/certify-shadow

## Universal Evaluation Design

Each opportunity is processed in this sequence:

1. Engine routing key resolution.
2. Specialist analysis with domain-specific criteria.
3. Universal Loki objections and fragility checks.
4. Universal Norns forecast labels (MODEL_ESTIMATE / NOT_YET_CALIBRATED).
5. Normalized dimension scoring across capital, speed, margin, downside, automation, owner-time, scalability, and strategic fit.
6. Weighted rank synthesis for cross-engine comparability.
7. Pantheon governance pass/fail and severity aggregation.
8. Best-option selection or abstention.
9. Owner envelope generation with decision rationale.

## Specialist-Per-Engine Behavior

The pipeline uses specialist analysis templates keyed by engine family so opportunity comparisons remain cross-engine while preserving engine-specific logic.

Examples include:

- real estate: structure around deal mechanics, downside containment, and execution friction
- digital products / SaaS: retention, churn-risk, delivery cost, and technical build burden
- automation services: adoption friction, implementation effort, support load, recurring potential

## Universal Pantheon Governance

The universal flow keeps the existing governance spirit while standardizing output into a shared structure:

- overall_allowed
- worst_severity
- blocked_by
- per-god checks and reasons

This allows one decision grammar to rank and filter opportunities regardless of engine origin.

## Abstention Rule

The pipeline explicitly supports abstention when all candidates fail deployment confidence thresholds or governance/safety constraints.

Certification includes an abstention proof case in the JSON artifact with no selected deployment option.

## Shadow Safety

Shadow certification runs in simulation mode and captures side-effect counters. Expected values are zero for:

- external messages
- contract execution side effects
- irreversible ledger actions
- production mutation channels outside approved persistence boundaries

Result in artifact: external_effects_all_zero = true.

## Regression Evidence

Validated current vs baseline classification:

- completion registry suite (Phase Three branch): 47 passed, 0 failed.
- governance slice in current worktree: 20 failures, all 404 Not Found.
- governance slice in clean baseline worktree from origin/main: same 20 failures, same signature.
- full backend suite in current worktree: interrupted by 5 collection errors.
- full backend suite in clean baseline worktree: same 5 collection errors.

Classification:

- Introduced regressions from Phase Three changes: 0
- Governance 404 slice: PRE-EXISTING / ROUTE-MOUNT OR TEST-HARNESS MISMATCH
- Full-suite collection errors: PRE-EXISTING / IMPORT-CONTRACT AND SCHEMA-COLLECTION DEFECTS

## Certification Scope and Limits

Proven in this phase:

- universal ranking/evaluation path is implemented and exercised
- cross-engine audit and shadow certification endpoints are functional
- abstention behavior is available and evidenced
- no new regressions were introduced relative to baseline failure profile

Not proven in this phase:

- production external integrations or live finance effects (out of scope)
- pre-existing governance mount defects outside completion registry scope

## Required Artifacts

- docs/_phase3_universal_opportunity_certification.json
- docs/UNIVERSAL_OPPORTUNITY_PIPELINE.md (this file)

## Status Classification

- Phase Three universal opportunity pipeline: BUILT - NEEDS TESTING (full-repo harness remains pre-existing unstable)
- Completion registry Phase Three surface: PROVEN in local router-focused regression context
- System-wide governance slice outside this surface: PRE-EXISTING DEFECT (not introduced here)

## Operating diligence and first investigation

Checked November 24, 2026. Scope for this read-only rehearsal is Manitoba small-fleet maintenance administration. Public facts were read and paraphrased from independently operated sources. The integration test uses a disposable scope and local registry fixtures. The live source registry, customer data, and channel permissions are outside the rehearsal.

| Existing system | Connection and evidence gap |
|---|---|
| Discovery and Venture Foundry | Approved signed demand and procurement exports can enter the existing queue and wake specialist assignments. Public operating research previously had no version-bound path into the candidate. Operating diligence now joins the exact Foundry evidence, queues scoped specialist work, and refuses changed rights, citations, or expired sources. Broad proactive refresh still requires commissioned rights-approved feed or publisher identities and independent observation receipts. |
| Pantheon, Loki and Prime | Current diligence is visible in reports with role-specific review and research gaps. The existing independent Loki queue recomputes make-or-buy costs and challenges assumptions. Prime checks the exact report and current cited sources. The existing ODIN/NJORD identity mechanism is available. This rehearsal uses deterministic local lenses. Separate hosted operators, deep model-assisted domain work, and source adjudication remain open. |
| Opportunity economics and Product Foundry | Existing economics can compare declared scenarios and operating capital, with base/stress calculations. Diligence contributes costs, labor and dependencies, with explicit abstention where buyer evidence is absent. The existing source-to-outcome disposable operating path still requires the downstream exact selection, Loki disposition and standing mandate. There is no positive release from this research record. |
| Builder and procurement | The existing Builder supports governed, reviewed candidate work. Diligence compares internal build with obtaining an existing service, but creates no Builder task, procurement or code change. A repeated bottleneck and governed improvement proposal would supply evidence for a small import or export recipe. |
| Mimir and operations | The persisted research digest and reports can be reread, and Mimir already retains verified operating outcomes through the existing path. There is no observed pilot outcome here to put into a playbook, calibrate Norns or use as buyer evidence. Replay avoids repeating an unchanged research submission. Expired evidence holds the candidate. A measured search budget and autonomous stop rule for commissioned research runs remain open. |

### Verified operating context

| Facet | Evidence and implication |
|---|---|
| Work and regulations | Manitoba describes preventive maintenance, daily inspections and periodic mandatory inspection records for applicable regulated operations. Its trip-inspection regulation sets scope and exceptions. Workflow hypothesis is to import existing records, reconcile vehicle IDs, attach receipts and flag missing or overdue evidence. Carrier personnel retain responsibility for inspections, decisions about roadworthiness and sign-off. Confirm the carrier's actual scope, retention and audit workflow with its compliance representative. [Manitoba maintenance](https://www.manitoba.ca/mti/mcd/audits_investigations/audits/maintenance.html) · [Manitoba regulation](https://web2.gov.mb.ca/laws/regs/current/095-2008.php) |
| Customers and distribution | Start discovery with Manitoba-regulated for-hire or private fleets with roughly 5–25 vehicles and fragmented records. Size and pain are segment hypotheses. The Manitoba Trucking Association describes both carrier and private-fleet categories. An approved association or shop placement could support voluntary inbound research. Directory entries were neither copied nor contacted. Registration totals measure vehicles rather than buying organizations or addressable demand. [MTA membership](https://trucking.mb.ca/membership/member-categories/) · [Statistics Canada vehicle registrations](https://www150.statcan.gc.ca/n1/daily-quotidien/260922/dq260922c-eng.htm) |
| Competition and sales | Fleetio advertises $4 per vehicle per month for its entry annual band, with a $5 monthly option, and Whip Around advertises paid plans starting at $5 per asset per month. Displayed vendor prices are context only. Check currency, tax, terms, data exports and exact cohort price before using a quote. Existing per-asset tools lower the odds that generic reminders alone justify a new subscription. The fleet buyer, procurement process, willingness to pay and product switching costs remain unverified. [Fleetio](https://www.fleetio.com/pricing) · [Whip Around](https://www.whip-around.com/faq/) |
| Operations, automation and failure | Test structured CSV import, alias matching, duplicate detection, dated evidence, renewal reminders, access revocation and audit export using synthetic fleet records. Stop on unresolved ID mismatch, unsupported records, export failure or permission loss. Keep a named fleet representative for regulatory decisions and a scoped implementation/support operator for exceptions. These controls are proposed safeguards for the candidate, and fleet workflow performance is unmeasured. |

### Compare two approaches

CAD planning assumptions. Contribution includes declared delivery, tool and acquisition costs and lane-level monthly overhead. Taxes, working capital, actual subscription churn and signed provider or customer terms are outstanding. The scenario is a sensitivity calculation, and the two approaches are commercially unvalidated.

| Approach | Offer and deal structure | Base contribution | Downside and dependencies |
|---|---|---:|---|
| Managed setup using existing software | CA$750 per fleet for a fixed migration, discrepancy list, customer-owned platform setup and accepted export. Customer owns vendor subscription and controls its data. | CA$275 per setup after 6 hours at CA$60, CA$25 in tools and CA$90 acquisition. Two setups less CA$150 fixed costs yield CA$400 monthly. | One setup taking 9 hours with CA$150 acquisition yields **−CA$115 per month** after fixed costs. Requires approved delegated vendor access, scoped operator, export rights and exact contract terms. |
| Purpose-built audit export subscription | CA$129 per fleet per month for evidence intake, reminders and an audit export, with cancellation and export rights. Define support, deletion and handoff before offering it. | CA$37 per fleet after 1 hour at CA$60, CA$12 tools and fees, and CA$20 amortized acquisition. Twelve fleets less CA$200 fixed costs yield CA$244 monthly. | Eight fleets with 1.5 support hours and CA$35 amortized acquisition yield **−CA$264 per month**. Requires validated recurring pain, tenant isolation, migration, regression coverage, customer support and service continuity. |

For the narrower tool-path comparison, the executable fixture uses explicit setup, recurring cash and loaded labor assumptions. Build totals CA$8,640 in year one. Buy totals CA$2,200 with a customer-paid platform subscription. These totals are separate tool-path assumptions. They should not be added to the lane contribution figures without reconciling overlapping labor and costs. A real approved quote, customer acceptance, and operator availability could reverse the recommendation.

**Disposition: abstain from commercial selection and dispatch.** Existing software plus managed setup is the first *research question* because a bounded setup is cheaper to validate than building a new platform. The public sources establish an operating context. They provide no observed conversion, willingness to pay, support time or renewals. Loki's digest-bound challenge flags these gaps and requires independent comparison of labor, provider terms and failure handling.

A subsequent permission-based pilot is a separate acceptance step. Set an approved budget, scope and maximum duration first. Compare current workflow and willingness to adopt both approaches, record consent and withdrawals, and measure import success, operator time and real commitments separately from expressed interest. Stop that lane if permission is withdrawn, a critical evidence or provider gate fails, or the tested price leaves nonpositive contribution after delay, acquisition and support. Keep customer contact, paid tooling, Builder implementation, payments and live delivery behind their existing approval boundaries.

**Reproduce the internal connection.** On a disposable checkout, run `python -m pytest -q services/api/tests/test_economic_control.py -k industry_diligence`. The regression exercises registered source references, idempotent replay, exact version and legacy scope, ODIN/NJORD event reports, separately authenticated Loki receipt, comparative abstention and citation withdrawal. Original public page access was manual research and is independent of the disposable fixture.
