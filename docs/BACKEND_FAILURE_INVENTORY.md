# BACKEND FAILURE INVENTORY

Generated: 2026-10-11T06:15:38.800639+00:00

## Baseline (Historical)
- Total: 913
- Passed: 242
- Failed: 465
- Errors: 188
- Skipped: 18
- Failed+Error results: 653

## Current Wave Two Inventory (Run A)
- Total: 913
- Passed: 319
- Failed: 415
- Errors: 161
- Skipped: 18
- Failed+Error results: 576
- Root-cause cluster count: 15
- UNKNOWN count: 0

## Current Classification Summary
- TEST_HARNESS_DEFECT: 260
- OBSOLETE_TEST: 255
- ENVIRONMENT_DEFECT: 53
- TEST_DATA_DEFECT: 8

## Current Cluster Summary
| cluster_id | count | class |
|---|---:|---|
| TEST_SETUP_CHAIN_FAILURE | 121 | TEST_HARNESS_DEFECT |
| ROUTER_404_CONTRACT_DRIFT | 119 | TEST_HARNESS_DEFECT |
| LEGACY_PACK_STRUCTURE_ASSERTS | 85 | OBSOLETE_TEST |
| LEGACY_PACK_EXPANSION_ASSERTS | 75 | OBSOLETE_TEST |
| LEGACY_BACKEND_PACKAGE_PATH | 61 | OBSOLETE_TEST |
| SQLITE_JSONB_COMPILE_ERROR | 40 | ENVIRONMENT_DEFECT |
| LEGACY_CORE_GOV_PATH | 34 | OBSOLETE_TEST |
| EXTERNAL_CONNECT_REFUSED | 13 | ENVIRONMENT_DEFECT |
| INTAKE_PARSER_STALE_API | 10 | TEST_HARNESS_DEFECT |
| LEADCREATE_VALIDATION_CONTRACT | 8 | TEST_DATA_DEFECT |
| DEAL_MODEL_ARGUMENT_CONTRACT_DRIFT | 4 | TEST_HARNESS_DEFECT |
| DEAL_BUYER_SCHEMA_RUNTIME_DRIFT | 2 | TEST_HARNESS_DEFECT |
| STATE_KEY_MISSING_SOURCE_LIFECYCLE | 2 | TEST_HARNESS_DEFECT |
| BUYER_MODEL_ARGUMENT_CONTRACT_DRIFT | 1 | TEST_HARNESS_DEFECT |
| STATE_KEY_MISSING_REMINDER_ID | 1 | TEST_HARNESS_DEFECT |

## TrustEventLog Signature Reconciliation
- ORIGINAL_TRUSTEVENTLOG_SIGNATURE_COUNT_AFTER_WAVE2: 0
- TRUSTEVENTLOG_NODE_COUNT_WITH_NEW_UNDERLYING_FAILURES: 7
- NEW_CLUSTER_ASSIGNMENTS_FOR_THE_7_NODES:
- services.api.tests.test_deal_lifecycle::test_lifecycle_action_orchestrates_flows -> DEAL_MODEL_ARGUMENT_CONTRACT_DRIFT (TypeError: 'org_id' is an invalid keyword argument for Deal)
- services.api.tests.test_deal_lifecycle::test_lifecycle_available_actions_at_stage -> DEAL_MODEL_ARGUMENT_CONTRACT_DRIFT (TypeError: 'org_id' is an invalid keyword argument for Deal)
- services.api.tests.test_deal_lifecycle::test_lifecycle_run_invalid_action -> DEAL_MODEL_ARGUMENT_CONTRACT_DRIFT (TypeError: 'org_id' is an invalid keyword argument for Deal)
- services.api.tests.test_deal_lifecycle::test_lifecycle_status_new_deal -> DEAL_MODEL_ARGUMENT_CONTRACT_DRIFT (TypeError: 'org_id' is an invalid keyword argument for Deal)
- services.api.tests.test_fake_live_operating_day::test_fake_live_operating_day_controlled_stage_report -> BUYER_MODEL_ARGUMENT_CONTRACT_DRIFT (TypeError: 'full_name' is an invalid keyword argument for Buyer)
- services.api.tests.test_flow_lead_to_deal::test_flow_lead_to_deal_basic -> DEAL_BUYER_SCHEMA_RUNTIME_DRIFT (sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: buyers)
- services.api.tests.test_flow_notifications::test_notify_deal_parties_seller_and_buyers -> DEAL_BUYER_SCHEMA_RUNTIME_DRIFT (sqlalchemy.exc.PendingRollbackError: This Session's transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (sqlite3.OperationalError) no such table: buyers)

## Launch Router Signature Reconciliation
- Baseline MISSING_LAUNCH_ROUTER_NAMES count: 14
- Current signature count: 0

## STATE_KEY_MISSING Final Classification
- SOURCE_LIFECYCLE_STATE_KEY_CLASSIFICATION: TEST_HARNESS_DEFECT
- REMINDER_ID_STATE_KEY_CLASSIFICATION: TEST_HARNESS_DEFECT
