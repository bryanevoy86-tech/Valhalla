# BACKEND DEFECT BURNDOWN

Generated: 2026-10-10T22:09:37.683729+00:00

## Baseline
- Failed/Error results: 653
- Totals: 913 total / 242 passed / 465 failed / 188 errors / 18 skipped
- Cluster count: 14
- UNKNOWN before triage: 264

## Classification After Canonical Triage
- OBSOLETE_TEST: 339
- TEST_HARNESS_DEFECT: 179
- ACTUAL_PRODUCTION_DEFECT: 73
- ENVIRONMENT_DEFECT: 53
- TEST_DATA_DEFECT: 8
- OTHER_PROVEN_CLASS: 1
- UNKNOWN after triage: 0

## Production Defect Claim Review
- Prior claim of 73 production-defect results was not 73 independent defects.
- Independent production-defect clusters at baseline: 2
- MODEL_REGISTRY_CONFLICT_TRUSTEVENTLOG: 70
- STATE_KEY_MISSING: 3

## Wave-One Repairs
- Repair applied: fully-qualified SQLAlchemy relationship targets for TrustEventLog in pack_ta and relationships models.
- Repaired clusters: MODEL_REGISTRY_CONFLICT_TRUSTEVENTLOG
- Post-fix gate status: collection=0 errors, Phase Two PASS, Phase Three PASS, Winnipeg PASS, Shadow safety PASS.

## Full Suite After Wave One
- Run A: 913 total / 242 passed / 465 failed / 188 errors / 18 skipped
- Run B: 913 total / 242 passed / 465 failed / 188 errors / 18 skipped
- Fresh DB repeatable: YES
- New regressions by failing node-id: 0
- Removed failing node-id count: 0

## Cluster Delta (Baseline -> Wave One)
- MODEL_REGISTRY_CONFLICT_TRUSTEVENTLOG: 70 -> 0 (delta -70)
- UNCLASSIFIED: 1 -> 71 (delta +70)
