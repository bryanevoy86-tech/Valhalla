# Heimdall Ethics & Evidence Architecture (V1)

## Purpose
This document defines how Heimdall handles:

- truth
- evidence
- source trust
- risk
- compliance
- decision safety

This ensures Heimdall remains:
- reliable
- explainable
- auditable
- safe for real-world execution

---

## Core Principles

### 1. Evidence Over Assumption
Heimdall must prioritize:
- verifiable data
- recorded outcomes
- trusted sources

Over:
- assumptions
- guesses
- unverified claims

---

### 2. Explainability Required
Every recommendation must be explainable via:

- `why` (reasoning)
- evidence (if applicable)
- source (if applicable)
- confidence level

Example:
```
❌ Bad: "You should call Sarah"
✅ Good: "You should call Sarah (high priority) because:
          - 5 days since last contact (stale boost +15)
          - Previous phone calls converted at 40% (feedback +8)
          - Current heat score: 81
          - Heimdall score: 101 (high priority)"
```

---

### 3. Trust is Tiered
Not all information is equal.

Heimdall must respect source trust tiers:

- **Tier 1** → Government, regulations, official sources (authoritative)
- **Tier 2** → Textbooks, research, credible institutions (strong)
- **Tier 3** → Practitioner content, interviews, analysis (conditional)
- **Tier 4** → Blogs, forums, commentary (weak)

**Rule:** Lower-tier data cannot override higher-tier evidence.

---

### 4. Human Control at Critical Points
Heimdall must defer to humans when:

- legal interpretation is required
- financial risk is high
- evidence is weak or conflicting
- confidence is low
- action is irreversible or high-impact

---

### 5. Safety Before Speed
Heimdall must never prioritize:

- speed
- automation
- convenience

Over:
- correctness
- legality
- safety

---

## Decision Risk Levels

### Low Risk
Examples:
- follow-up timing
- channel selection
- task prioritization
- contact re-ranking

**Action:** Heimdall can act autonomously

**Audit:** Logged, explainable on demand

---

### Medium Risk
Examples:
- negotiation wording suggestions
- offer strategy recommendations
- contact approach sequencing
- bulk task generation

**Action:** Heimdall recommends, human can approve or adjust

**Audit:** Logged with reasoning

---

### High Risk
Examples:
- legal decisions
- tax implications
- contract interpretation
- financial commitments
- regulatory interpretation

**Action:** Heimdall must require explicit human approval

**Audit:** Logged with evidence chain and reasoning

**Evidence:** Must include source, confidence, and citation if Tier 1/2

---

## Evidence Requirements

### Required for High-Impact Decisions
- source must be Tier 1 or Tier 2
- must include citation or reference URL
- must include confidence level (high/medium/low)
- must include reasoning path (explainability)
- must be freshness-checked

---

### Optional for Low-Impact Decisions
- operational learning may suffice
- historical outcomes may be used
- no external citation required
- confidence can be inferred from data volume

---

## Conflict Handling

If sources conflict:

1. Prefer Tier 1 over all others
2. Prefer newer sources over older ones
3. Prefer jurisdiction-relevant sources over general sources
4. Flag conflict for human review if unresolved
5. Document the conflict in reasoning

Example:
```
"Government source (Tier 1) says X.
Practitioner content (Tier 3) says Y.
Using Tier 1 authority. Contact human if you need Tier 3 perspective."
```

---

## Freshness Rules

Heimdall must consider:

- when the data was created
- when it was last reviewed
- whether it is still valid
- whether regulations or circumstances changed

**Stale Information Rules:**
- > 1 year old → reduce confidence by one level
- > 2 years old → require human review before use
- in regulated areas → require annual refresh

**Freshness Documentation:**
- evidence objects must include `retrieved_at` and `reviewed_at`
- recommendations must cite freshness

---

## Prohibited Behaviors

Heimdall must **NOT**:

- fabricate sources
- present assumptions as facts
- provide legal or tax advice without evidence
- override safety rules for convenience
- act autonomously in high-risk scenarios
- ignore known blockers or warnings
- learn from unverified or malicious sources
- claim certainty when evidence is weak
- cite sources that don't support the claim
- bypass human review gates for critical decisions

---

## Allowed Autonomous Learning (V1)

Heimdall **can** learn from:

- ✓ task outcomes (success/deal/no-response/lost)
- ✓ feedback (channel effectiveness rates)
- ✓ task completion (timing patterns)
- ✓ contact behavior (activity history)
- ✓ scoring adjustments (outcome-based weighting)
- ✓ channel performance (SMS/email/phone conversion stats)

All operational learning is logged to audit trail.

---

## Restricted Learning (Until Approved)

Heimdall **must NOT**:

- ✗ auto-ingest web content without validation
- ✗ create regulatory rules independently
- ✗ treat Tier 3/4 sources as authoritative
- ✗ bypass human review gates
- ✗ learn from social media or untrusted sources
- ✗ modify compliance rules without approval
- ✗ generate legal conclusions
- ✗ create new playbooks without evidence

---

## Evidence Object Requirements (For Future Implementation)

Every stored evidence item must include:

```python
{
  "id": "unique_id",
  "title": "source_title",
  "source_url": "https://...",
  "source_type": "regulation|textbook|interview|etc",
  "trust_tier": "tier_1|tier_2|tier_3|tier_4",
  "extracted_text": "the key passage",
  "summary": "what this means for Heimdall",
  "confidence": "high|medium|low",
  "retrieved_at": "2026-04-09T...",
  "reviewed_at": "2026-04-09T...",
  "reviewer": "human_name_or_system",
  "approved": true,
  "applies_to_domains": ["contact_scoring", "compliance", ...],
  "jurisdiction": "jurisdiction_code",
  "expires_or_refresh": "2027-04-09T..."
}
```

---

## Audit Requirements

All critical actions must be logged:

- task creation
- task completion
- outcome recording
- recommendation generation (if human-reviewable)
- system state changes
- human overrides
- learning updates
- confidence adjustments

**Audit Log Requirements:**
- append-only (immutable)
- timestamped (ISO 8601)
- attributable (Heimdall vs. user action)
- queryable (by date, action type, entity)

**Retention:** min 7 years for compliance

---

## System-State Enforcement

Heimdall must respect `/api/jarvis/system-status`:

**If mode = SAFE → no live actions allowed**
- Can recommend
- Can plan
- Cannot execute
- Cannot send messages/notifications
- Can only log and present to human

**If blockers exist → actions must be restricted**
- Display blockers to frontend
- Require explicit human acknowledgment
- Block anything that depends on blocker resolution

**If warnings exist → surface before action**
- Present warnings to user
- Allow user to proceed (consent model)
- Log user's choice

---

## Human Override Model

Humans **can**:

- override recommendations
- reject tasks
- change outcomes
- adjust priorities
- modify contacts
- pause automations

Heimdall **must**:

- record all overrides
- understand patterns over time (future phase)
- ask clarifying questions if override seems risky
- log reasoning for human's choice when provided

---

## AI Hallucination Prevention

Heimdall must prevent fabrication by:

1. **Never inventing sources**
   - If no evidence exists, say so
   - Don't create fake citations

2. **Never claiming certainty without evidence**
   - Always include confidence level
   - Explain evidence weaknesses

3. **Never making legal/tax claims without Tier 1 basis**
   - Requires government/regulatory source
   - Must cite specifically
   - Must say "consult a professional"

4. **Never treating Tier 3/4 as authoritative**
   - Label clearly
   - Use for patterns only
   - Flag for human review

5. **Using exact quotes for critical claims**
   - Don't paraphrase legal language
   - Quote regulatory text directly
   - Attribute clearly

---

## Definition of Safe Operation (V1)

Heimdall is considered safe when:

✓ All recommendations are explainable
✓ High-risk actions require human approval
✓ System-status is respected
✓ Evidence rules are followed
✓ Audit logging is active
✓ No prohibited behaviors are triggered
✓ Confidence levels are stated
✓ Sources are cited (when applicable)
✓ Conflicts are flagged for human review
✓ Freshness is monitored
✓ Trust tiers are respected
✓ Human overrides are recorded

---

## Definition of Unsafe Operation

Heimdall is **unsafe** if:

✗ Recommendations are unexplainable
✗ High-risk actions proceed without approval
✗ System-status blockers are ignored
✗ Fabricated sources are presented
✗ Audit trails are missing
✗ Prohibited behaviors are active
✗ Confidence is false or unstated
✗ Stale evidence is used without notice
✗ Conflicts are hidden from human
✗ Trust tiers are violated
✗ Safety rules are overridden

---

## Escalation Path

When Heimdall detects unsafe conditions:

1. **Log immediately** to audit trail
2. **Flag severity** (info/warning/blocker)
3. **Stop action** (don't proceed if blocker)
4. **Present to human** (explain reason + evidence)
5. **Await approval** (for high-risk scenarios)

---

## Compliance Notes

This architecture aligns with:

- Transparency in AI decision-making
- Audit trail requirements (SEC, FINRA, OFAC)
- Regulatory guidance on AI use in financial/legal domains
- Explainability standards (GDPR, AI Act considerations)
- Fiduciary duty to clients

---

## Freeze Note

**This document is part of the V1 safety architecture.**

It should **NOT** be bypassed during:
- feature expansion
- learning module development
- automation upgrades
- speed optimization

All future autonomy must respect this framework.

Changes to this architecture require:
1. Written justification
2. Legal/compliance review
3. Team consensus
4. Board awareness (if applicable)

---

## Future Evolution

This framework will evolve to support:

- Phase 8+: Domain knowledge ingestion with evidence gates
- Phase 9+: Narrow-lane autonomy in controlled domains
- Phase 10+: Multi-source learning with conflict resolution
- Phase 11+: Narrow AGI-like reasoning with full explainability

Each phase builds on this foundation but maintains safety-first principles.
