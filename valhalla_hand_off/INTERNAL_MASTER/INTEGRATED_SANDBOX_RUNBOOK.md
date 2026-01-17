# Integrated Sandbox Runbook (INTERNAL)

## Goal
Simulate multiple engines concurrently under one global sandbox with:
- DRY-RUN ON
- Outbound OFF
- Shared resource constraints
- Cycle-by-cycle integrated reporting

## Start
1) Ensure .env.sandbox has:
   VALHALLA_PHASE=3
   VALHALLA_REAL_DATA_INGEST=1
   VALHALLA_DRY_RUN=1
   VALHALLA_DISABLE_OUTBOUND=1

2) Run:
   python SANDBOX_INTEGRATED.py

## Outputs
- reports/integrated_sandbox/INTEGRATED_<timestamp>.json
- reports/integrated_sandbox/engine_exports/*

## Add a new engine
1) Create sandbox_profiles/<engine_name>.py with get_engine()
2) Add it to configs/sandbox_integrated.json with enabled=false
3) Solo-sandbox it first, then set enabled=true
4) Observe integrated reports for contention effects

## Non-negotiables
- Never enable outbound in integrated sandbox
- Never disable DRY-RUN in integrated sandbox
- Never activate multiple new engines at the same time
