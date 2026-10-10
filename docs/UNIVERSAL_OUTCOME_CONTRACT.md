# Universal Outcome Contract

## Purpose
Standardize what is recorded at decision time so every opportunity can be reconciled later by Mimir learning.

## Decision-Time Required Fields
- Identity: `decision_id`, `opportunity_id`, `engine_id`, `legacy`, `jurisdiction`
- Classification: `outcome_class`
- Traceability: `prediction_timestamp`, `prediction_locked_at`, `evidence_snapshot_id`, `pantheon_snapshot_id`
- Decision: `heimdall_decision`
- Expecteds: `expected_economics`, `expected_timing`, `expected_risk`, `expected_exit_path`
- Observability: `outcome_observability_state`

## Outcome-Time Fields (initially null at decision time)
- `actual_outcome`
- `actual_outcome_date`
- `actual_economics`
- `actual_timing`
- `outcome_confidence`
- `prediction_error`
- `decision_quality`
- `role_accuracy`

## Contract States
- `SHADOW_OUTCOME`: no live side effects expected
- `HISTORICAL_OUTCOME`: replayed historical path
- `LIVE_OUTCOME`: reserved for future controlled launch gate

## Current Status
- Emitted for generic and real-estate paths in Phase 3 evaluate flow.
- Verified in focused route tests.
