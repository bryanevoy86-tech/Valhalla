# COMPLEXITY BUDGET

Complexity is a finite resource.

The system has limited capacity to absorb new complexity without sacrificing stability.

---

## Core Principle

**Every new engine, feature, or system consumes complexity.**

Complexity must earn return on that investment.

---

## Rules

### 1. Every Addition Has a Cost

**Cost of adding Engine B:**
- Mental model of how B works
- Integration points with A
- Failure modes involving A+B
- Debugging effort when something breaks
- Documentation burden
- Training (if others involved)

### 2. Complexity Must Earn ROI

**Question before adding:**
- Does this return > complexity cost?
- Could I scale existing engines instead?
- Is this the most efficient use of complexity budget?

**If not clearly yes:** Don't add it.

### 3. Complexity Audits Occur Periodically

**Quarterly review:**
- Count active engines
- Measure coupling (how intertwined are they?)
- Assess mental overhead
- Evaluate returns
- Identify simplification opportunities

### 4. Simplification Is Always Encouraged

**When complexity grows:**
- Kill weak engines first
- Consolidate where possible
- Remove integrations that aren't earning return
- Simplification counts as a success

---

## Warning Signs

Watch for these patterns:

### Too Many Small Additions

**Problem:**
- 5 new engines in 3 months
- Each seemed small
- Combined they exceed capacity

**Fix:** Pause additions. Consolidate or simplify.

### Increasing Mental Overhead

**Signs:**
- Harder to remember how everything works
- More time explaining systems to self
- More mistakes due to misunderstanding interactions

**Fix:** Document or simplify.

### Unclear Failure Modes

**Problem:**
- Can't explain what breaks if Engine B fails
- Cascading failures hard to predict
- Debug time increasing

**Fix:** Reduce coupling or increase isolation.

### Tight Coupling Between Engines

**Warning:**
- Engine B depends on Engine A succeeding
- One failure cascades to others
- Hard to test independently
- Impossible to kill one without affecting others

**Fix:** Add isolation or reduce coupling.

---

## Complexity Budget by Phase

### Phase 3 (Current)

**Complexity budget:** 3 engines max  
**Current:** Valhalla Core (1 engine)  
**Remaining capacity:** 2 engines  

**Rule:** Do not add more than 2 additional engines during Phase 3.

### Phase 4 (After 72-hour cert)

**Complexity budget:** 5-7 engines max  
**Starting:** 1 core + up to 2 new (from Phase 3)  
**Capacity:** 3-5 more engines  

**Rule:** Do not exceed 7 engines without simplification.

### Phase 5+ (Scale phase)

**Review complexity budget:**
- Evaluate how much operator bandwidth exists
- Measure if consolidation is needed
- Adjust rules based on actual vs. planned

---

## Operator Bandwidth Is The Real Constraint

**Real limit is NOT technical capacity. It's operator bandwidth.**

**Operator bandwidth consumed by:**
- Monitoring systems
- Making decisions
- Debugging failures
- Learning new engines
- Context switching

**Warning sign:** Operator says "This is getting overwhelming."

**Action:** Pause growth immediately. Simplify or consolidate.

---

## Complexity Debt

**Just like technical debt, complexity can accumulate.**

**Complexity debt occurs when:**
- Too many loose integrations
- Unclear failure modes
- Maintenance burden exceeds value
- System feels fragile

**Paydown options:**
1. Kill weak engines
2. Consolidate redundant systems
3. Document thoroughly
4. Simplify integrations

---

## Simplification Examples

**Instead of adding Engine 4, consider:**

1. **Kill Engine 3** (weak performer)
   - Frees complexity budget
   - Simplifies system
   - Reallocates resources to Engine 2

2. **Consolidate Engines 1+2** (if overlap exists)
   - Reduce coupling
   - Single mental model
   - Easier to maintain

3. **Wait** (for Engine 4 to mature)
   - Reduce risk
   - Allow current engines to scale
   - Return to growth later

---

## Decision Rule

**Before adding complexity:**

Ask: "Is this in the top 3 highest-return opportunities?"

**If yes:** Can proceed if budget allows.  
**If no:** Suggested alternatives:
1. Scale existing engine instead
2. Kill underperforming engine first
3. Wait until higher-priority work complete

---

## Heimdall's Role

Heimdall flags:
- Complexity budget exceeded
- New addition not earning return
- System approaching fragility threshold
- Opportunities for simplification

**Heimdall can recommend pause.** Operator makes final call.

---

## Review Cadence

- **Weekly:** Monitor active complexity (is it stable?)
- **Monthly:** Assess returns (is ROI positive?)
- **Quarterly:** Full audit (is budget sustainable?)
- **Annually:** Strategic review (should we adjust budget?)

---

*Complexity growth is the #1 reason systems become fragile. Guard the budget.*
