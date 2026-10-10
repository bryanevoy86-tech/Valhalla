# Champion Challenger Protocol

## Objective
Support controlled comparison between current champion logic and challenger logic without live execution risk.

## Current Enforcement
- `decision_model` accepted values:
  - `CHAMPION`
  - `CHALLENGER`
- Challenger is enforced as shadow-only.
- Request with `decision_model=CHALLENGER` and `shadow_mode=false` returns `409`.

## Required Comparison Tracking
- `decision_model` returned in each evaluation.
- Shared outcome contract schema across champion/challenger paths.
- Shared replay partition and leakage protection metadata.

## Promotion Guard
Challenger promotion requires:
1. No holdout contamination.
2. Better or equal baseline-adjusted regret profile.
3. No increase in critical pantheon blocks.
4. Explicit owner approval before any live path enablement.
