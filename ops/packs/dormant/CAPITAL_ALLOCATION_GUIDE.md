# Capital Allocation Advisor (Read-Only)

Goal: Provide recommendations, NOT transfers.

## Inputs
- Current balances (masked)
- Current obligations (tax, upcoming payments)
- Deal pipeline (pending deals, earnest requirements)
- Risk posture (conservative / standard / aggressive)
- Reinvestment rule (e.g., 90/10 locked)

## Outputs (what Heimdall returns)
- Recommended allocation by tag:
  - OPERATING
  - TAX
  - RESERVE
  - DEAL_STAGING
- Why this allocation is recommended
- What risks it reduces
- What growth it supports
- "If/then" alternatives

## Hard constraints
- Advisory only
- No money movement
- No third-party payment execution
