# Loki — Independent Adversarial AI God (Sovereign Decision Challenger)

**Status:** CONTRACT / PARTIAL SOURCE / UNCONNECTED INDEPENDENT AUDITOR.
**Owner doctrine:** Loki challenges Heimdall, rather than merely producing a confidence or risk score.

## Sovereign intent and responsibilities

Loki is the second AI God with independent review standing. He receives a locked, source-grounded copy of Heimdall's proposal and authorized independent evidence, attacks assumptions, calculations, legal and tax positions, contracts, deals, trust/funding flows, code, automation and catastrophic downside. He identifies problems Heimdall missed, presents counterevidence and sends an immutable dissenting report to the owner. Heimdall may answer the critique with evidence, but cannot silently delete it.

Independent review standing does NOT authorize Loki to move funds, sign documents, modify trusts, generate binding contracts, approve his own findings, rewrite original proposals, execute external actions, deploy production, or bypass owner/professional decisions.

### Mandatory controlled review chain

1. Heimdall produces a versioned immutable proposal plus source evidence.
2. Isolated Loki receives the actual snapshot rather than a persuasive summary. He may request authorized additional sources.
3. Loki independently stress-tests the claims, errors, contracts, economics, regulatory exposure, catastrophic risks, objections, alternative approaches and unknowns.
4. A controlled Pantheon Bridge routes the evidence through Odin (alignment), Norns (forecast), Forseti (contradiction resolution), Tyr (legal/ethical review) and other approved specialists without unrestricted agent-to-agent tool calls.
5. Heimdall responds, revises or withdraws; Loki re-audits meaningful human or AI edits.
6. The owner sees Heimdall's position AND Loki's dissent, critical evidence, disagreement, worst cases, uncertainty, proposed corrections, Norns results, and options A/B/C/Override.
7. Owner retains final strategy authority subject to enforceable law/safety/professional review; Loki cannot self-approve or directly act.
8. Mimir records predicted versus observed outcomes and whether Loki's objection proved material; REAL and SHADOW outcomes remain distinct.

### Review categories

- **Reasoning / numbers:** false assumptions, hallucinated source claims, hidden constraints, calculations, cash flow, strategy comparison.
- **Contracts / legal:** contradictory clauses, bad protections, missing licensing, tax-evasion/fraud risk, undisclosed obligations and expert sign-off.
- **Wealth / trust / residency:** ownership, trustee and beneficiary mismatches, cash-value or policy-loan interest and repayment, tax consequences, Canadian residency ties, liquidity, overleverage and estate exposure.
- **Autonomous businesses:** spoofed permissions, prompt injection, wrong provider, fraud, retries, double billing, stale sources, outages, escalation and irreversibility.
- **Commercial model:** price, demand, churn, acquisition costs, hidden recurring costs, staffing, competition, owner workload and opportunity cost.
- **Systemic protection:** Shield, Black Ice, privacy, credential leaks, cross-tenant access, backups, rollback and systemic blast radius.

### Mandatory review triggers

Binding contracts, trust/estate and residency changes, insurance and policy loans, major investments, externally committed capital, regulated work, professional tax/legal interpretation, employment/termination, production code/deployment, irreversible customer data, material business launch, acquisition, high-risk trading/arbitrage, or system-wide incident.

Lightweight routine internal work can use preapproved deterministic boundaries without expensive full independent inference, but the same model may never downgrade its own high-impact work to avoid Loki review.

### Required audit evidence

- Audit ID, immutable Heimdall proposal ID and SHA-256, snapshot/version, business/tenant/jurisdiction, audit reviewer/version and timing.
- Independent evidence sources, citations, dates, provenance and access rights; identify conflicts and uncertainty.
- For each objection: specific Heimdall claim, contrary evidence, assumption, evidence for/against, downside, materiality, likely failure mode, proposed correction and unresolved status.
- Financial/operational worst plausible cases, exit plan, impact/recovery estimates and calibrated confidence if available.
- Green/Yellow/Red risk, verdict APPROVE / APPROVE_WITH_EDITS / REJECT / INSUFFICIENT_EVIDENCE, corrective options, owner questions, required professional input and immutable record of resolved/unresolved disagreements.
- Evidence of the actual independently executed reviewer and a trustworthy verification receipt. A model-generated flag saying independent_audit_verified=true is not evidence.

Missing, failed, timed-out or unverified Loki review must return a blocked/held state. Never report Completed on a stub.

## Actual code found as of Nov 19/20

1. services/api/app/routers/governance_loki.py: deterministic downside, ruin, correlation, complexity thresholds; 18 passing original Pantheon API tests include this layer. NOT independent deep analysis.
2. services/api/app/ai/agents/loki.py: simple risk-score / transaction-size conservative rules. Not a real attack on Heimdall reasoning.
3. services/api/app/core/loki_engine.py: source explicitly calls itself a heuristic text-analysis stub; text/keyword-length confidence does not amount to verified audit.
4. services/api/app/services/universal_opportunity_evaluator.py: in-process universal_loki_objections returns material/critical objections and can force research-more/reject. Useful integration but not a separate independent auditor.
5. services/api/app/routers/loki.py: legacy review creation previously marked generic placeholder audit COMPLETED; now returns HTTP 503 while independent audit engine absent. Final verdict endpoint now refuses self-asserted success; history is not recertified.
6. services/api/app/routers/governance_orchestrator.py: five original gods callable together. This is not yet proof that every external dispatch passes through the Pantheon.

## Acceptance before Loki is integrated / complete

1. Durable independent audit queue, actual independent audit worker and trusted source verification; no fake success or self-issued approval.
2. High-risk operations MUST be held until review finishes and all material issues have an evidence-backed resolution or explicit lawful owner/expert disposition.
3. Demonstrate three adversarial cases: attractive but arithmetically false business plan; contradictory binding contract or trust/residency structure; profitable-looking venture that fails crash/outage/replay or worst-case market test.
4. Re-run independent Loki after a meaningful Heimdall/human change to amount, clause, opportunity, model, external provider or risk.
5. Test critical dissent propagation to owner A/B/C/Override report and actual effect guard, with Loki timeout/absence failing closed.
6. Run malicious-source, forged flag, collision, duplicate, worker-death, legal/cross-tenant privacy, source-withholding and false confidence tests; then controlled PostgreSQL/staging/live proof.

The independent auditor is not complete merely because original five-god rules pass. No production, insurer, bank, tax or legal operations were performed during this correction.
