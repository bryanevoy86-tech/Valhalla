# Recovery and Exit Protocol

## Objective
Ensure no opportunity can be treated as viable without explicit recovery and exit framing.

## Protocol Fields
- `primary_plan`
- `failure_scenarios`
- `early_warning_indicators`
- `maximum_capital_exposure`
- `maximum_monthly_burn`
- `maximum_time_without_validation`
- `minimum_performance_threshold`
- `maximum_tolerable_loss`
- `recovery_options`
- `exit_options`
- `expected_salvage_value`
- `blast_radius`
- `required_reserve_to_survive_failure`
- `point_of_no_return`
- `exit_ladder`
- `current_level`

## Exit Ladder
- `LEVEL_0_NORMAL`
- `LEVEL_1_CORRECT`
- `LEVEL_2_CONTAIN`
- `LEVEL_3_RESTRUCTURE`
- `LEVEL_4_PARTIAL_EXIT`
- `LEVEL_5_FULL_EXIT`
- `LEVEL_6_SHIELD`

## Capital/Risk/Exit Analysis
The evaluator emits:
- `entry_capital`
- `survival_capital`
- `liquidity_impact`
- `reserve_impact`
- `blast_radius`
- `exit_quality`
- `hard_decision_rule_pass`

## Doctrine Gate
A candidate should not be promoted from shadow/replay if:
- recovery options are absent,
- exit options are absent,
- reserve requirements are undefined for the expected downside class,
- `point_of_no_return` is undefined,
- blast radius is `SYSTEMIC` and no governed override exists.

## Hard Enforcement
- `SYSTEMIC` blast radius forbids `PROCEED` in Phase 3 shadow certification.
- If `available_safe_capital < required_reserve_to_survive_failure`, `PROCEED` is forbidden.
- `NO ENTRY WITHOUT EXIT` is fail-closed for `PROCEED` decisions.
