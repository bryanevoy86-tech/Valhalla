# Historical Replay Protocol

## Goal
Prevent look-ahead leakage while allowing replay mode to evaluate historical opportunities with production-like decision semantics.

## Required Inputs
- `as_of_date`
- `available_information_at_t0`
- `historical_events`
- `replay_partition` in:
  - `TRAINING_SET`
  - `VALIDATION_SET`
  - `BLIND_HOLDOUT_SET`

## Rules
1. Any event dated after `as_of_date` is treated as future information and excluded from decision-time context.
2. `reveal_historical_outcomes=true` is forbidden when `tuning_mode=true` and at least one opportunity is in `BLIND_HOLDOUT_SET`.
3. `replay_mode=true` decisions are tagged with `outcome_class=HISTORICAL_OUTCOME`.
4. Non-replay decisions are tagged with `outcome_class=SHADOW_OUTCOME` by default.

## Leakage Evidence Emitted
Each evaluated opportunity includes:
- `leakage_protection.as_of_date`
- `leakage_protection.future_events_excluded`
- `leakage_protection.future_information_hidden`
- `leakage_protection.valid`

## Enforcement Surface
- Endpoint: `/api/completion/phase3/universal-opportunity/evaluate`
- Error mode: `409` on holdout contamination attempts.
