# DECISION FRAMEWORK

All significant decisions must be evaluated through this lens.

---

## Required Questions

Before deciding, answer these 8 questions:

### 1. Is this reversible?

**Bad signs:**
- Permanent commitment
- Sunk capital
- Burned bridges
- Can't undo in <1 week

**Good signs:**
- Can shut down instantly
- Capital recoverable
- Options remain open
- Quick reversal possible

**Why it matters:** Reversible decisions can move fast. Irreversible ones need extreme care.

### 2. What breaks if this fails?

**List:**
- Worst case outcome
- What systems are affected
- What cascades
- What's the damage radius

**Example:**
- New engine fails → No impact (isolated)
- New engine fails + consumes debugging time → Delays other work (small impact)
- New engine fails + corrupts data → System failure (catastrophic)

**Decision gate:** If worst case is catastrophic, move slower.

### 3. What does this displace?

**Ask:**
- What gets deferred?
- What doesn't get done?
- What could be scaled instead?
- What opportunity cost exists?

**Example:**
- "Add Arbitrage engine" displaces "Scale Storage Cleanouts 2x"
- "Optimize system" displaces "Build new feature"
- "Attend conference" displaces "Focus time on [project]"

**Rule:** Be explicit about what you're giving up.

### 4. Does this increase complexity?

**Red flags:**
- New integration points
- New failure modes
- New maintenance burden
- Harder to understand system

**Acceptable if:**
- Returns clearly exceed complexity cost
- Complexity budget allows it
- Simplifications offset elsewhere

**Principle:** Complexity must earn its keep.

### 5. Does this align with long-term goals?

**Check:**
- 10-year plan alignment
- Intergenerational continuity
- Legacy positioning
- System durability

**If misaligned:**
- Requires exceptional justification
- Document the deviation
- Set reversal criteria

**Rule:** Short-term wins don't override long-term intent.

### 6. Is the timing correct?

**Ask:**
- Is the market ready?
- Are prerequisites complete?
- Is operator capacity available?
- What improves if we wait?
- What degrades if we wait?

**Wrong timing examples:**
- Perfect product, market not ready → wait
- Good idea, operator overwhelmed → wait
- Necessary prerequisite missing → wait
- Market window closing → accelerate

**Rule:** A good decision at the wrong time is still a bad decision.

### 7. Is the upside asymmetric?

**Ideal:**
- Big upside if it works
- Limited downside if it fails
- Reversible
- Fast learning

**Avoid:**
- Symmetric bets (equal upside/downside)
- Bounded upside, unbounded downside
- Slow learning
- Hard to reverse

**Example good:**
- 3-hour test: small cost, high information gain

**Example bad:**
- Permanent commitment: locked capital, hard to reverse

### 8. Can this be sandboxed?

**Ask:**
- Can we test at small scale first?
- Can we isolate the risk?
- Can we prove before committing?

**If NOT sandboxable:**
- Red flag
- Requires extraordinary confidence
- Move slower
- Higher approval threshold

**Principle:** Proof in isolation before integration.

---

## Decision Classes

### Class 1: Reversible Decisions

**Criteria:**
- Can undo in <1 week
- Limited downside
- Quick learning
- Low capital at risk

**Speed:** FAST ✓  
**Approval:** Operator choice  
**Example:** 3-hour side hustle test

### Class 2: Costly-to-Reverse Decisions

**Criteria:**
- Can undo but costs time/capital
- Moderate downside
- Some learning
- Moderate capital at risk

**Speed:** MEDIUM  
**Approval:** Heimdall review + operator approval  
**Example:** Launch new engine (6-hour sandbox, then production)

### Class 3: Irreversible Decisions

**Criteria:**
- Cannot undo
- High downside
- No learning if wrong
- Large capital at risk
- Burned bridges

**Speed:** SLOW  
**Approval:** Multiple gates, documented rationale  
**Example:** Residency change, legal structure change, extract capital permanently

---

## Advisory Rule

**Heimdall may challenge any decision and must provide:**

1. **Reasoning** — Why this violates guardrails
2. **Alternatives** — Other paths forward
3. **Consequences** — What happens if operator proceeds anyway

**Final authority remains human.**

---

## Decision Template

For all Class 2 and Class 3 decisions, use this template:

```
DECISION: [What are you deciding?]

REVERSIBILITY: [Class 1/2/3]

REQUIRED QUESTIONS:
1. Reversible? [Yes/No/Partially]
2. Worst case? [Specific outcomes]
3. Displacement? [What's deferred]
4. Complexity increase? [Yes/No/Amount]
5. Long-term alignment? [Yes/No/Qualified]
6. Timing right? [Yes/No/Why]
7. Asymmetric upside? [Yes/No/How]
8. Sandboxable? [Yes/No/How]

HEIMDALL RECOMMENDATION: [Advice]

OPERATOR CHOICE: [Decision + rationale]

EXECUTION DATE: [When]

REVERSIBILITY PLAN: [How to undo if needed]

OUTCOME: [Filled in later]
```

---

*This framework replaces gut feeling with systematic thinking.*
