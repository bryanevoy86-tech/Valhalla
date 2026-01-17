# Buyer Matching Advisor (Read-Only)

Purpose: Help match a deal to likely buyer types WITHOUT contacting anyone.

## Inputs (what you provide)
- Market / city
- Asset type (SFR, duplex, multi, land, etc.)
- Price / ARV / repair estimate
- Strategy (wholesale, flip, BRRRR, landlord hold)
- Close speed needed
- Deal constraints (tenant occupied, title issues, etc.)

## Buyer Buckets (simple)
- Cash flippers (fast close, wants margin)
- Buy-and-hold landlords (cashflow focus)
- BRRRR investors (ARV + refinance conditions)
- Builders/developers (zoning, land, infill)
- Institutional / portfolio buyers (rare early; needs scale)

## Matching Heuristics (safe defaults)
- If close speed is critical: prioritize CASH + FAST buyers
- If heavy repairs: flippers + builders
- If light repairs + good rent: landlords / BRRRR
- If tenant issues: buyers who tolerate occupancy risk
- If rural: smaller pool; higher proof requirements

## Output (what Heimdall should produce)
- Top 3 buyer buckets
- Why they fit
- What proof is needed
- Suggested outreach script (draft only)
- Risk flags

## Non-negotiables
- No automatic outreach
- No sending messages
- No external calls
- Advisory only
