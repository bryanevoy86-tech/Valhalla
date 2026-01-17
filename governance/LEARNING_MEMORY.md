# LEARNING & MEMORY

The system must remember so the operator does not have to.

Failure is data. Mistakes are acceptable. Repeating them is not.

---

## Core Principle

**The system has a longer memory than the operator.**

Every failure should produce a lesson.

Every lesson should be stored and referenced.

---

## Requirements

### 1. Every Failed Engine Produces a Postmortem

**When an engine is killed or fails:**

Create a 1-page postmortem (see ENGINE_KILL_RULES.md):

```
ENGINE: [Name]
DURATION: [How long it ran]
OUTCOME: [Archive/Failure/Pivot]

WHAT WE LEARNED:
1. [First lesson]
2. [Second lesson]
3. [Third lesson]

WHY IT DIDN'T WORK:
[Clear explanation]

IF WE TRY THIS AGAIN:
[One specific change]
```

**Storage:** `/governance/postmortems/[engine_name].md`

### 2. Lessons Are Stored and Indexed

**Postmortem database:**
- Organized by lesson type
- Cross-referenced
- Searchable by keyword
- Updated when new data arrives

**Example index:**
- Complexity pitfalls
- Timing mistakes
- Integration issues
- Capital allocation errors
- Operator bandwidth traps

### 3. Similar Ideas Trigger Warnings

**When new engine proposed that resembles a failed one:**

Heimdall surfaces past lesson:

"This engine resembles Engine X (archived 2025-11-15). 
Key lesson: [What went wrong]. 
Apply that learning here."

---

## Lessons Database

**Track by category:**

### Complexity Lessons
"Adding integrations without removing old ones → System fragility"
"5+ engines with tight coupling → Debugging nightmare"

### Timing Lessons
"Forced scaling before market ready → Poor results"
"Delayed action when market window obvious → Missed opportunity"

### Resource Lessons
"High-effort, low-return engine → Opportunity cost"
"Manual tasks instead of automation → Burnout"

### Integration Lessons
"New engine coupled to core → Cascading failures"
"Unclear failure modes → Debug time explosion"

### Capital Lessons
"Over-extraction → Reduced compounding"
"Illiquid capital deployment → Reduced flexibility"

### Operator Lessons
"Ignored fatigue signals → Decision quality dropped"
"Too many decision windows → Context switching overload"

---

## Memory Protocol

### When Something Fails
1. Document the failure (postmortem)
2. Extract the lesson
3. Store it
4. Share it (if relevant to operators)

### When Similar Idea Emerges
1. Heimdall searches memory
2. Flags similar past failure
3. Surfaces the lesson learned
4. Operator acknowledges or overrides

### When Pattern Emerges
1. Note if same mistake has happened 2+ times
2. Flag as "Recurring risk"
3. Escalate to operator
4. Consider systemic fix

---

## Postmortem Examples

### Example 1: Complexity Overload

```
ENGINE: Multi-Integration Dashboard
DURATION: 3 weeks
OUTCOME: Archive

WHAT WE LEARNED:
1. Adding 5 data sources simultaneously → Debugging nightmare
2. Tight coupling to core system → One failure cascades
3. No isolation testing → Failure discovered in production

WHY IT DIDN'T WORK:
System wasn't ready for that level of integration.
Tried to do too much at once.
No incremental testing.

IF WE TRY THIS AGAIN:
Test each data source independently first.
Couple to core system one at a time.
Prove each integration works before adding next.
```

### Example 2: Forced Timing

```
ENGINE: Real Estate Arbitrage
DURATION: 2 months
OUTCOME: Archive

WHAT WE LEARNED:
1. Market timing was off → Low deal flow
2. Forced execution despite signals → Wasted time
3. Ignored "wait" recommendation → Poor results

WHY IT DIDN'T WORK:
Market wasn't developed enough.
We pushed ahead anyway.
Predictably poor results.

IF WE TRY THIS AGAIN:
Wait for deal flow signal to be clear.
Don't force execution on tight timeline.
Let market maturity guide decision, not schedule.
```

### Example 3: Operator Overload

```
ENGINE: Manual Lead Qualification
DURATION: 1 month
OUTCOME: Automated

WHAT WE LEARNED:
1. Repetitive manual decisions → Decision fatigue
2. Ignored "automate this" signals → Burnout
3. High cognitive load → Lower quality decisions

WHY IT DIDN'T WORK:
System depended on operator heroics.
Operator got tired and made mistakes.
Work quality declined.

IF WE TRY THIS AGAIN:
Automate from the start.
Don't accept manual repetition.
Operator bandwidth is precious.
```

---

## Recurring Pattern Response

**If same mistake happens twice:**

1. Document both instances
2. Flag as "Recurring risk"
3. Operator reviews
4. Create specific guard

**Example:**
- Mistake 1: Engine killed because of tight coupling
- Mistake 2: Different engine killed for same reason
- Response: Create coupling audit in sandbox testing

---

## Heimdall's Memory Role

Heimdall maintains:
- Database of all postmortems
- Index of lessons by category
- Tracker of recurring patterns
- Alert for similar situations

**When new decision proposed:**
Heimdall checks: "Have we done this before? What happened?"

---

## Learning Velocity

**Good system:**
- Mistakes → rapid learning
- Lessons applied to next similar situation
- No repeat failures

**Bad system:**
- Mistakes → no documentation
- Similar failure happens again
- Operator surprised ("Didn't we learn this?")

**Measure:** "How long until similar mistake is repeated?"

- <3 months: System learning is working
- 3-6 months: OK
- >6 months or repeats: Problem

---

## Memory Integration

**Document storage:**
```
/governance/
  /postmortems/
    engine_name_1.md
    engine_name_2.md
  /lessons_index.md (searchable summary)
  LEARNING_MEMORY.md (this file)
```

**When to review:**
- Weekly: Check for new postmortems
- Monthly: Index updates
- Quarterly: Pattern analysis
- Annually: Strategic learning review

---

## Principle

**Mistakes are tuition. Make sure we graduate.**

A system that forgets its lessons is a system doomed to repeat them.

---

*Documentation costs time now. Preventing repeated mistakes saves time later.*
