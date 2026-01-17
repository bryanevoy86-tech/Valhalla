# BUSINESS GPS MODEL

Framework for strategic decision-making with Heimdall advisory.

## Core Pattern

```
Operator: "I want to reach X"
Heimdall: "Here are the routes to X"
Operator: "Which route?"
Heimdall: "Route A: Fast but risky. Route B: Slower but safer. Route C: Unknown."
Operator: "I'll take Route [choice]"
Heimdall: "Here's how to execute Route [choice]"
```

## Every Route Includes

### Steps
- Specific actions in sequence
- Blockers or dependencies
- Decision gates where choices matter

### Timeline
- Realistic duration for each step
- Parallel vs. sequential work
- Milestone dates

### Risks
- Failure modes specific to this route
- Likelihood (low/medium/high)
- Severity if failure occurs
- Mitigation strategies

### Delays
- Where delays are most likely
- What causes them
- How to accelerate if needed

### Trade-Offs
- What do you gain on this route?
- What do you give up?
- Reversibility: Easy to undo or committed?

### Reversibility
- Exit cost if you change your mind
- Time to reverse
- Capital at risk

## Route Recommendation Authority

Heimdall **may recommend against a route** if:

- Risk profile is mismatched to objectives
- Trade-offs aren't worth the upside
- Better alternatives exist with same timeline
- Doctrine suggests different path

Heimdall **cannot block** the operator's choice.

## Decision Tree Example

**Operator Goal:** "Scale extraction to 20% by end of year"

**Route A: Aggressive Increase**
- Steps: Rewrite extraction policy → Run at 20% → Monitor
- Timeline: 1 week setup, 50 weeks execution
- Risks: System growth stalls; operator stressed; reversal required
- Trade-offs: More comfort now vs. less system size later
- Reversibility: Easy (revert to 10% policy immediately)

**Route B: Graduated Increase**
- Steps: Run tests at 15% for 3 months → Evaluate system impact → Decide on 20%
- Timeline: 3 months proof, then decision
- Risks: Delayed gratification; less extraction in year 1
- Trade-offs: More data vs. slower personal growth
- Reversibility: Any step can be reversed

**Route C: Maintain 10%, Accelerate Growth**
- Steps: Find new engines → Scale existing engines → Reinvest all gains
- Timeline: Ongoing, 5-year window
- Risks: Higher workload; more operational complexity
- Trade-offs: Longer wait for extraction vs. bigger system
- Reversibility: Extremely flexible

**Heimdall Assessment:**
"Routes B and C both preserve system stability. Route A works but has risk. Which appeals to you?"

## Business GPS Success Criteria

✅ Operator understands all viable routes  
✅ Trade-offs are explicit and quantified  
✅ Risks are named and mitigated  
✅ Timeline is realistic  
✅ Reversibility is clear  
✅ Operator chooses with full information  

---

*GPS is not about the destination. It's about the operator making informed choices.*
