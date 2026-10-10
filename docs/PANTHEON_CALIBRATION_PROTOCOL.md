# Pantheon Calibration Protocol

## Purpose
Track model confidence, uncertainty, and decision quality drift over time.

## Calibration Fields in Current Contract
- `norns.model_state`
- `norns.calibration_state`
- `norns.probability_of_worthwhile_validation`
- `norns.probability_of_first_revenue`
- `norns.probability_of_break_even`
- `norns.probability_of_repeatable_profitability`

## Baseline Comparison Outputs
- `baseline_comparison.rule_based_property_model`
- `baseline_comparison.simple_payback_ranking`
- `baseline_comparison.simple_margin_capital_ranking`
- `baseline_comparison.industry_average_heuristic`

## Regret Ledger Output
- `decision_regret.regret_class`
- `decision_regret.confidence`
- `decision_regret.delta`

## Promotion Expectation
A model candidate is not PROVEN until it demonstrates calibrated probability behavior against blinded outcomes and does not degrade baseline-adjusted regret.