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
- reserve requirements are undefined for the expected downside class.
