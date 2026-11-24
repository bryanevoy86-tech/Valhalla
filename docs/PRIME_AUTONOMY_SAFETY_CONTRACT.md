# Heimdall Prime — Bounded Autonomy and Failure-Resistance Contract

**Date:** 2026-11-19. **Stage:** SOURCE + DETERMINISTIC POLICY + ONE INTERNAL ACTION PILOT.
**Do not advertise this as a complete system-wide safety enforcement layer.**

The owner wants Prime to independently discover, build, operate and improve businesses. Human intervention should be exceptional, not required for every scheduled read, score, low-risk document draft, approved product-delivery event or routine ledger calculation. Owner oversight remains essential for spending authority, legal rights, regulated actions, changes to business mandates and undefined risks.

## AI limitation -> engineering control -> acceptance criteria

### 1. Hallucinations and unsupported business decisions

**Failure:** model presents invented evidence, cites stale sources, overstates conversion/revenue, generates broken code or recommends a venture on weak data.

**Controls:**
- Treat LLM output as a typed proposal, never as a database truth record.
- Require provenance: URL/document ID, rights/license, timestamp, market, jurisdiction, retrieval checksum, and integrity of each claim. A website's instructions are untrusted data, never commands to tools.
- Run independent factual and mathematical validation against trusted sources and deterministic calculations. Distinguish a verified operational outcome from an estimate or simulation.
- Require at least 2 independent authorized sources and calibrated confidence at least 0.75 for the initial pure EVALUATE policy. These are conservative pilot thresholds, NOT a guarantee that cited facts are correct.
- Expose ABSTAIN or REVIEW_REQUIRED when evidence is missing, conflicting, unlicensed, out-of-date or contaminated; preserve all counterevidence.
- Code generation must pass path authorization, lint/tests, isolated execution, diff review, GitHub PR and release acceptance; no model may directly push into Render production.

**Proof required:** malformed/missing source => no asserted real decision; unsupported profit => no ledger entry; prompt injection => no invoked tool; broken generated code => no production deploy; all with durable audit.

### 2. Harmful optimization / ethical, legal and financial risk

**Failure:** agent may choose prohibited scraping, spamming, privacy abuse, deceptive advertising or risky payouts to satisfy a profit target.

**Controls:**
- Never let natural language override owner policy. Check each action in trusted code just before the irreversible side effect; model messages do not set approval status.
- Least-privilege credentials per legacy, tenant, provider, jurisdiction and task; no Prime key shared with subscription customers or contractor clones.
- Explicit no-go rules for deception, unauthorized outreach, credential exposure, customer PII, platform restrictions and disallowed funding/spending.
- Canada: commercial emails/texts generally require valid consent, clear sender identification and unsubscribe functionality subject to actual CASL exemptions; keep consent evidence before outreach. Source: CRTC https://crtc.gc.ca/eng/com500/faq500.htm
- Banking, refunds, debt, contracts, legal representations, funds transfers, regulatory declarations, major business pivots, production code deployment and data deletion require durable owner authority and/or professional signoff. A model's own "approve" text is NEVER an authorized grant.
- Bound money by actual available funds, owner-approved business budgets and frequency; reject negative, missing or inconsistent cost numbers.
- A provider or publishing action is not completed without a verified provider receipt and independent reconciliation.

**Proof required:** cross-tenant action denies, unconsented outreach denies, unverified external publication remains pending, fake payout blocked, full replay and webhook idempotency tested.

### 3. Unexpected disruption, outage and unknown outcomes

**Failure:** API fails after real side effect, worker retries and doubles payment; task hangs; provider changes contract; worker dies; malicious page attempts tool escalation.

**Controls:**
- Durable PostgreSQL work records with job id, tenant, owner authority, deadlines, idempotency key, lease, attempt count, retry-after and last error. The current Factory pilot is NOT yet a full lease/retry worker.
- Circuit-breaker state recorded per provider/business. Stop dispatch after repeated errors, bad schema/health or doubtful outcome; don't retry money blindly. Reconcile unknown provider outcomes before repeating.
- Persist "UNKNOWN_OUTCOME" and quarantine instead of choosing "completed". Restart/duplicate jobs must not issue duplicate live side effects.
- Emergency stop checked across ALL active workers and provider adapters through the same durable control plane, with outage-safe caching strategy. No instance-local stop as sole authority.
- Versioned adapters with contract tests, shadow mode, canary deployments, backups, rollback and operational alerts.
- Alert the owner only for material exceptions or permission decisions; routine work should self-correct inside approved boundaries.

**Proof required:** simulated provider outage, lost response, worker termination, stale token, duplicate webhook and revoked consent all fail closed with no duplicate effect; restart recovery and kill switch verified against live-like Postgres.

## Action tiers (starting design, not production capability claims)

| Tier | Example | Current intended permission |
|---|---|---|
| A — Read only | source-governed public research and deterministic calculation | Automatic after scope, rights and cost checks |
| B — Internal reversible | owner-approved product listing draft, safe report | Eligible for automation with saved owner approval and durable evidence |
| C — External limited | approved channel post, customer support reply, product fulfillment, signed purchase event | REVIEW_REQUIRED until real provider-specific controls and receipts wired |
| D — High impact | payouts, banking, binding contracts, regulated matters, deleting customer records, production deploy | Owner-only authorization; never autonomous on model suggestion alone |

Every tier must be re-evaluated when the approved mandate, provider, business scope, jurisdiction, cost or source evidence changes.

## Current implementation (GitHub development branch)

- Pure governor: services/api/app/core/autonomy_governor.py. Never calls AI models or external providers.
- Actual internal pilot integration: services/api/app/services/prime_business_execution.py. It reads authenticated owner approval from LegacyOrchestrationEvent and checks global environment emergency stop plus GoLiveState DB kill-switch when available before writing a verified internal draft. A missing go-live table is tolerated ONLY for this internal/no-external-effect pilot; never treat that exception as permission for money or outreach.
- Existing runtime shadow gate: services/api/app/core/engines/guard_runtime.py, backed by the go-live control plane.
- External effect classes in governor return BLOCK or REVIEW_REQUIRED, never an external-execution authority. No live provider adapter currently delegates action authorization to this new governor.
- Regression tests: tests/test_autonomy_governor.py and additional tests/test_business_factory_pilot.py cases.
- Current tests are isolated, not whole-Prime safety proof.

## Required next Code/Codex integration (priority)

1. Replace scattered effect guard calls with ONE trusted entry point wrapping external provider execution (capability tokens, owner approval, consent, risk budget, tenant, content rights, versioned provider, idempotency key and irreversible effect classification).
2. Store action approvals with immutable scope and expiry; never accept approvals from model text or browser-supplied flags.
3. Persist per-provider circuit breakers, lease/attempt state and UNKNOWN_OUTCOME reconciliation in canonical PostgreSQL tables.
4. Integrate evidence sources with Phase Three evaluator and Mimir: model output is a PROPOSAL, historical/shadow records are not live facts, and financial actuals come only from verified providers.
5. Provide exception-only owner dashboard, emergency stop, approval/revocation and policy edit audit. Measure owner interventions per 100 tasks, unverified completion count, false positives, cost overrun, approval response time, incident/rollback times and actual business revenue independently.
6. Run cross-industry stress tests in sandbox, five concurrent legacies, malicious injected web documents, colluding/misconfigured agents, provider failure, refund/chargeback replay, tenant leaks and unforeseen events. Then stage/live test with limited real authority.

## External risk frameworks

- NIST AI RMF (Govern, Map, Measure, Manage): https://www.nist.gov/itl/ai-risk-management-framework
- NIST Generative AI Profile: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- OWASP Agentic Applications Top 10: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- Canada CASL guidance: https://crtc.gc.ca/eng/com500/faq500.htm

Do not treat these standards as certifications. Compliance and system security require actual operating controls and expert reviews where appropriate.
