# ENGINE TERMINATION RULES

Killing engines is a sign of system health.

A system that sheds weak ideas quickly is stronger than one that carries them forever.

---

## Core Principle

**Survival is earned, not granted.**

Engines must continuously justify their existence.

---

## Kill Criteria

An engine should be terminated if:

### 1. Low Signal After Sandbox Window

**Indicator:**
- Sandbox test completed
- Results: marginal, unclear, or negative
- No clear path to strong performance

**Decision:** Archive quietly. Move on.

### 2. High Friction Relative to Upside

**Indicator:**
- Requires constant babysitting
- Manual intervention needed regularly
- Operational overhead high
- Returns not proportional to effort

**Decision:** Is the friction worth the gain? If not, kill it.

### 3. Requires Heroics

**Indicator:**
- Only works if operator maintains intense focus
- Falls apart if attention lapses
- Designed as if operator has infinite energy

**Problem:** System should NOT depend on heroics.

**Decision:** If heroics are required, not sustainable.

### 4. Distracts From Load-Bearing Engines

**Indicator:**
- Requires debugging time that impacts core systems
- Mental bandwidth diverted
- Prevents scaling better opportunities
- Opportunity cost is high

**Decision:** Kill it. Focus on what matters.

### 5. Poor System Fit

**Indicator:**
- Integrations are awkward
- Failure modes cascade into core system
- Hard to isolate
- Requires workarounds elsewhere

**Decision:** If it doesn't fit, remove it.

### 6. Better Alternative Exists

**Indicator:**
- Similar goal, different approach
- New approach is simpler
- New approach has clearer upside
- Can't run both (complexity budget)

**Decision:** Kill the old one. Promote the new.

### 7. Operator Doesn't Believe In It

**Indicator:**
- Operator is halfhearted
- "Good idea but..." justifications
- Not excited anymore
- Energy has shifted elsewhere

**Decision:** Kill it. Don't carry skepticism forward.

---

## Kill Decision Process

### Step 1: Identify Candidate
Engine meets one or more kill criteria.

### Step 2: Rapid Assessment
- Is there ANY reason to keep it?
- Are the returns genuinely marginal or just slower?
- Is this a timing issue or a fundamental problem?

### Step 3: Make Decision
- [ ] KEEP (with clear justification)
- [ ] THROTTLE (reduce to minimal resources)
- [ ] ARCHIVE (terminate)

### Step 4: If Archive
1. Stop all new work immediately
2. Document final state
3. Write 1-page postmortem
4. Store lesson learned
5. Shut down cleanly

### Step 5: Reindex
- Complexity budget updated
- Resources reallocated
- Operator bandwidth recovered

---

## Postmortem Template (One Page)

```
ENGINE: [Name]
DURATION: [How long it ran]
OUTCOME: Archive

WHAT WE LEARNED:
1. [One specific thing]
2. [One specific thing]
3. [One specific thing]

WHY IT DIDN'T WORK:
[2-3 sentence explanation]

IF WE TRY THIS AGAIN:
[One change that would help]

RESOURCE IMPACT:
- Complexity budget freed: [amount]
- Operator time freed: [hours/week]
- Capital recovered: [amount]
```

---

## Avoid These Mistakes

### ❌ Sunk Cost Bias
"We've invested so much, we can't kill it now."

**Counter:** Past investment doesn't justify future waste.

### ❌ Emotional Attachment
"This was my idea, so it must work."

**Counter:** Killing your own ideas is a sign of maturity.

### ❌ Waiting Too Long
"Let's give it one more quarter."

**Counter:** Signal is usually clear. Delay wastes resources.

### ❌ No Postmortem
Kill it quietly, learn nothing, repeat mistake later.

**Counter:** Every failure teaches something valuable.

### ❌ Gradual Starvation
Leave it running on minimal resources, check in never.

**Counter:** Either commit or kill. Half measures waste complexity budget.

---

## Heimdall's Role

Heimdall flags:
- Engines that should be killed
- Sunk cost bias creeping in
- Emotional attachment preventing good decisions
- Lesson learned from previous failures being ignored

**Heimdall recommendation:** "This meets kill criteria #2, #4, #6. I recommend archive."

**Operator decision:** Keep, throttle, or archive.

---

## Cultural Norm

**Killing engines should be celebrated, not hidden.**

- "We killed Engine X because it wasn't earning its complexity cost."
- "This is why we kill fast: we learned the signal in 6 hours instead of 6 months."
- "Archiving this freed us to scale the engine that's actually working."

**In healthy systems, termination is success.**

---

## Kill Velocity Metric

**Measure system health by kill speed:**

- Weak idea → recognized in <3 days = Excellent
- Weak idea → recognized in <1 week = Good
- Weak idea → recognized in >1 month = Concerning
- Weak idea → never killed = System problem

**Faster killing = faster learning = better compounding.**

---

*Killing weak ideas protects the system. Archive without drama. Learn the lesson. Move on.*
