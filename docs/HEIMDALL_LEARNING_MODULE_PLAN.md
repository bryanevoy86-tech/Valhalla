# Heimdall Learning Module Plan (V1 Architecture)

## Purpose
This document defines the first learning architecture for Heimdall.

It does NOT implement the full ingestion engine yet.
It defines:
- allowed knowledge sources
- evidence categories
- learning flow
- confidence rules
- human review triggers
- what should and should not be automated

---

## Learning Goals

Heimdall must eventually improve in these areas:

- action recommendation
- contact scoring
- channel selection
- task prioritization
- outcome interpretation
- negotiation support
- trusted knowledge retrieval
- evidence-backed guidance

---

## Learning Layers

### Layer 1 — Operational Learning
This is already partially active.

Inputs:
- task completion
- recorded outcomes
- feedback history
- channel effectiveness
- action counts
- status transitions

Purpose:
- improve next-actions
- improve scoring
- improve channel recommendations

Status:
- **ACTIVE / PARTIALLY BUILT**

---

### Layer 2 — Domain Knowledge Ingestion
This is planned but not yet built.

Inputs:
- trusted websites
- official government sources
- regulations
- textbooks
- vetted training materials
- domain transcripts / notes
- structured internal business rules

Purpose:
- improve knowledge-backed recommendations
- support legal/regulatory awareness
- support negotiation and business guidance
- reduce hallucination risk with evidence rules

Status:
- **PLANNED**

---

### Layer 3 — Human Performance Learning
This is planned but not yet built.

Inputs:
- human negotiator transcripts
- human follow-up notes
- buyer/seller interaction patterns
- conversion outcomes
- objection/response pairs

Purpose:
- teach Heimdall real-world decision patterns
- improve recommendation quality
- prepare future narrow-lane autonomy

Status:
- **PLANNED**

---

## Approved Source Categories

### Tier 1 — Highest Trust
Allowed:
- government websites
- official regulations
- official court / tax / compliance sources
- recognized standards bodies
- official platform documentation
- primary-source public filings

Examples:
- government regulations
- regulator publications
- tax authority guidance
- official docs for tools and APIs

Use Cases:
- compliance
- tax
- operational rules
- regulated decisions

---

### Tier 2 — Strong Trust
Allowed:
- textbooks
- peer-reviewed research
- university material
- credible industry bodies
- vetted training content from top operators

Use Cases:
- frameworks
- skill-building
- business methods
- negotiation theory
- domain best practices

---

### Tier 3 — Conditional Trust
Allowed only with caution:
- reputable operator content
- transcripts from successful practitioners
- interviews
- podcasts
- non-official industry analysis

Use Cases:
- pattern extraction
- objection handling
- sales tactics
- practical workflows

Rules:
- never use as sole authority for legal/tax/regulatory claims
- should support, not replace, Tier 1/2 evidence

---

### Tier 4 — Low Trust / Use Carefully
Examples:
- blogs
- forums
- unverified social posts
- general commentary

Rules:
- do not treat as authoritative
- do not use for final decision support in critical domains
- may be used only for weak-signal pattern spotting

---

## Knowledge Object Types

All ingested knowledge should eventually be stored in structured objects.

### 1. Rule Object
Fields:
- `id`: unique identifier
- `title`: short name
- `domain`: business domain
- `jurisdiction`: where this applies
- `source_url`: where it came from
- `summary`: key points
- `confidence`: high/medium/low
- `effective_date`: when it starts applying
- `expires_or_review_date`: when to refresh
- `citation_required`: boolean (legal/tax rules need this true)

Example:
A regulation or policy rule that Heimdall should follow.

---

### 2. Pattern Object
Fields:
- `id`: unique identifier
- `domain`: business domain
- `pattern_type`: recommendation/channel/outcome/etc
- `description`: what this pattern is
- `source_type`: tier 1/2/3/4
- `confidence`: high/medium/low
- `supporting_examples`: list of evidence
- `counter_examples`: when it doesn't apply

Example:
"Email outperforms SMS for this type of contact in this jurisdiction."

---

### 3. Playbook Object
Fields:
- `id`: unique identifier
- `domain`: business domain
- `title`: playbook name
- `trigger_condition`: when to use
- `recommended_steps`: the sequence
- `source_basis`: where it comes from
- `confidence`: high/medium/low
- `human_review_required`: boolean

Example:
A follow-up sequence or negotiation play that Heimdall can recommend.

---

### 4. Evidence Object
Fields:
- `id`: unique identifier
- `title`: document/source title
- `source_url`: where to find it
- `source_type`: tier 1/2/3/4
- `tier`: trust tier
- `extracted_text`: the key passage
- `summary`: what it means for Heimdall
- `retrieved_at`: when downloaded
- `reviewed_at`: when human verified
- `confidence`: high/medium/low

Example:
The raw evidence that supports a rule, pattern, or playbook.

---

## Confidence Rules

### High Confidence
Use when:
- multiple trusted sources agree
- evidence is recent enough
- evidence is relevant to jurisdiction/domain
- operational outcomes support it

Allow:
- direct recommendation
- autonomous action if within safe authority

---

### Medium Confidence
Use when:
- source quality is decent
- evidence is incomplete or somewhat old
- outcome history is limited

Allow:
- recommendation + caveat
- suggest human review option

---

### Low Confidence
Use when:
- source is weak
- evidence is contradictory
- evidence is stale
- only one weak source supports the claim

Require:
- human review before action
- clear explanation of uncertainty

---

## Human Review Triggers

Heimdall must escalate to human review when:

- confidence is low on an important recommendation
- legal or tax interpretation is involved
- regulatory sources conflict
- source freshness is questionable
- recommendation could create financial or compliance risk
- action would exceed safe authority
- emotional or negotiation volatility is unusually high
- evidence is insufficient for a final recommendation

---

## What Heimdall Can Learn Automatically (V1 Direction)

### Allowed:
- scoring adjustments from outcomes
- channel preferences from results
- simple recommendation weighting
- action ranking improvements
- contact-type effectiveness patterns
- feedback-driven scoring updates

### Not Yet Allowed:
- automatic rule creation in regulated areas
- final legal/tax conclusions without review
- autonomous ingestion from untrusted sources
- unrestricted web scraping
- replacing human approval on high-risk decisions
- generating new playbooks without review

---

## Learning Flow (Target Design)

### Operational Loop (ACTIVE NOW)
```
1. task created
2. task completed
3. outcome recorded
4. result stored
5. scoring adjusted
6. recommendations improve
```

### Knowledge Loop (PLANNED)
```
1. trusted source identified
2. source ingested
3. evidence extracted
4. evidence scored
5. rule/pattern/playbook candidate created
6. human review if needed
7. approved knowledge becomes usable
```

### Human Performance Loop (PLANNED)
```
1. human interaction captured
2. transcript or notes stored
3. objection/response extracted
4. outcome linked
5. pattern candidate created
6. approved for training use
```

---

## Initial Domains for Learning

Priority order for ingestion:

1. **Contact Scoring** — How to weight contacts
2. **Channel Recommendation** — When to use which channel
3. **Task Prioritization** — How urgent is urgent
4. **Follow-up Playbooks** — What to do next
5. **Negotiation Support** — How to handle objections
6. **Compliance/Evidence Support** — Legal and regulatory awareness
7. **Strategic Pattern Recognition** — Broader market patterns

---

## Freeze Notes

**This document defines the architecture only.**

It does not mean the full learning engine is built yet.

The first real learning already active is:
- outcome-based scoring adjustment (Phase 5)
- channel feedback learning (Phase 5)
- operational evidence capture (Phases 4-7)

Everything beyond that should be built in controlled phases.

---

## Definition of "Learning Module Started"

The learning module officially begins when all of these exist:

✓ Evidence object schema  
✓ Source trust tiers  
✓ Confidence rules  
✓ Human review triggers  
✓ At least one ingestion path  
✓ Approved storage pattern for learned objects  

Until then:
**Heimdall is learning operationally, but not yet ingesting domain knowledge at scale.**

---

## Phase Roadmap

### Phase 8 (Post V1)
- Evidence object storage
- First source ingestion path
- Human review workflow
- Tier 1 government source integration

### Phase 9+
- Tier 2 textbook/research integration
- Tier 3 practitioner content integration
- Pattern extraction pipeline
- Confidence scoring engine

### Future Phases
- Narrow-lane autonomy for specific domains
- Full knowledge graph
- Continuous learning feedback loops
