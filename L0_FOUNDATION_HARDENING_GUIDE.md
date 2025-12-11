# PACK L0-05 through L0-08 — Foundation Hardening Guide

## Status Overview

Your system already has substantial infrastructure in place:

### ✅ PACK L0-05: System Health / Status / Log Backbone — LARGELY COMPLETE

**Existing Implementation:**
- `system_health.py`: Model, router, schema, service ✓ (COMPLETE)
- `system_status.py`: Model, router, schema, service ✓ (COMPLETE)
- `system_log.py`: Model, router, schema, service ✓ (COMPLETE)

**Key Endpoints:**
- `/system-health/live` — Kubernetes liveness probe
- `/system-health/ready` — Kubernetes readiness probe
- `/system-health/metrics` — Application metrics
- `/system/status/` — System status + PACK registry
- `/system/logs/` — Structured audit logs with filtering

**Hardening Needed:**
1. Ensure all three work together coherently (correlation IDs, shared patterns)
2. Add comments marking stable contracts
3. Verify they're registered on main FastAPI app
4. Add minor type hints/docstrings where sparse

---

### 📋 PACK L0-06: Telemetry + Observability Wiring — PARTIAL FOUNDATION

**Existing Files:**
- `models/telemetry.py` (partial)
- `routers/telemetry.py` (partial)
- `schemas/telemetry.py` (partial)
- `observability/tracing.py` (partial)
- `observability/replay.py`, `scrub.py`, `retention.py`, etc. (scattered utility scripts)

**What's Needed:**
1. Consolidate TelemetryEvent model with required fields: id, timestamp, source, event_type, severity, payload (JSON), correlation_id, tenant_id
2. Wire telemetry endpoints to ingest + query events
3. Integrate tracing.py to create/attach correlation IDs to all requests
4. Turn scattered observability helpers into coherent modules plugged into telemetry pattern
5. Ensure system_log events generate telemetry entries automatically

---

### 🚦 PACK L0-07: Rate Limiting + Security Policy Surface — MOSTLY COMPLETE

**Existing Implementation:**
- `models/rate_limit.py` (COMPLETE)
- `routers/rate_limit.py` (COMPLETE)
- `schemas/rate_limit.py` (COMPLETE)
- `services/rate_limit.py` (COMPLETE)
- `models/security_actions.py` (COMPLETE)
- `routers/security_actions.py` (COMPLETE)
- `models/security_policy.py` (COMPLETE)
- `routers/security_policy.py` (COMPLETE)
- `routers/security_dashboard.py` (COMPLETE)

**What's Needed:**
1. Ensure backend/security/ratelimit.py + rl_helpers.py are wired as central helpers
2. Add middleware integration so rate limits are checked on every request
3. Security violations → telemetry/system_log entries
4. Verify security_dashboard aggregates and formats data for UI

---

### ⏱️ PACK L0-08: Jobs, Schedulers, System Checks — PARTIAL

**Existing Files:**
- `models/scheduled_job.py` (partial)
- `routers/scheduled_jobs.py` (partial)
- `models/system_check_job.py` (partial)
- `models/training_job.py` (partial)
- `scheduler/runner.py` (partial)
- `backend/app/core/rq.py` (partial)
- `workers/shield_worker.py`, `trust_worker.py`, `sla_worker.py` (partial)

**What's Needed:**
1. Clean up / finalize scheduled_job, system_check_job, training_job models + schemas
2. Implement queue adapter (RQ or other) in backend/app/core/rq.py
3. Implement scheduler/runner.py to enqueue and track jobs
4. Wire workers to execute jobs and report back via telemetry/system_log
5. Ensure job failures bubble up to system health dashboard

---

## Recommended Next Steps

### Phase 1: Harden L0-05 (Quick, ~1-2 hrs)
1. Review + add docstrings to system_health, system_status, system_log services
2. Ensure correlation_id is passed through all three modules
3. Add comments marking stable contracts (won't change casually)
4. Verify all routers are registered on main FastAPI app
5. Run basic integration test: hit all three endpoints, confirm they work together

### Phase 2: Wire L0-06 (Medium, ~3-4 hrs)
1. Solidify TelemetryEvent model with full schema
2. Implement telemetry router endpoints (ingest + query)
3. Add tracing middleware to generate correlation IDs on all requests
4. Update system_log service to auto-emit telemetry events for logged messages
5. Turn observability helpers into pluggable modules

### Phase 3: Integrate L0-07 (Medium, ~2-3 hrs)
1. Implement central rate limiting helper in backend/security/ratelimit.py
2. Wire rate limit checks into FastAPI middleware
3. Ensure rate limit violations → security_actions + telemetry
4. Update security_dashboard to aggregate recent violations and SLOs

### Phase 4: Build L0-08 (Larger, ~4-5 hrs)
1. Finalize job models + schemas
2. Implement queue adapter in rq.py (can use Redis + RQ or Celery)
3. Implement runner/worker loop
4. Wire job results → system_log + telemetry
5. Add test to create a job, check status, verify it completes

---

## Key Design Principles (All PACKs)

1. **Shared Patterns:**
   - All use correlation_id for tracing
   - All emit events to system_log or telemetry
   - All follow service → router → endpoint pattern

2. **Type Hints & Docstrings:**
   - Every endpoint has a clear docstring
   - Services are fully typed
   - Comments mark stable vs. experimental APIs

3. **No Secrets in Code:**
   - All config via settings/environment
   - Never log passwords, API keys, or PII
   - Telemetry/logs are "safe to share"

4. **Coherence:**
   - Each PACK solves one problem cleanly
   - No overlapping responsibilities
   - Layers depend upward, not downward

---

## File Locations Quick Reference

| PACK | Key Files |
|------|-----------|
| **L0-05** | `routers/system_health.py`, `routers/system_status.py`, `routers/system_log.py` |
| **L0-06** | `routers/telemetry.py`, `services/system_introspection.py`, `observability/*.py` |
| **L0-07** | `routers/rate_limit.py`, `routers/security_policy.py`, `routers/security_dashboard.py`, `backend/security/ratelimit.py` |
| **L0-08** | `routers/scheduled_jobs.py`, `scheduler/runner.py`, `backend/app/core/rq.py`, `workers/*.py` |

---

## When Ready: Signal to Proceed

Once you've reviewed this, let me know which PACK(s) to tackle first, or if you want me to run the hardening for all four in sequence.

Recommend order: **L0-05 → L0-06 → L0-07 → L0-08** (from simplest to most complex).
