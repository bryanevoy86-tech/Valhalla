# ROUTER REGISTRATION LOGGING

## Implementation

Updated `app.core.router_registry.py` include_router_safe() function to provide explicit startup logging.

### Logging Strategy

Each router registration now logs in two channels:
1. **Console (print)** - Immediate visible feedback during startup
2. **Logging (log)** - Structured logs for aggregation/monitoring

### Console Output Format

#### Success (green signal)
```
[app.main] Registered router: {name} ({module}:{attr}) prefix={prefix}
```

Example:
```
[app.main] Registered router: heimdall (app.routers.heimdall:router) prefix=/api
[app.main] Registered router: audit (app.routers.audit:router) prefix=/api
[app.main] Registered router: operational_dashboard (app.routers.operational_dashboard:router) prefix=/api
```

#### Warning (optional router failed)
```
[app.main] ⚠️  ROUTER_FAIL: {name} ({module}:{attr}) -> {exception_type}: {exception_message}
```

Example:
```
[app.main] ⚠️  ROUTER_FAIL: some_optional_router (app.routers.some_optional_router:router) -> ImportError: No module named 'app.routers.some_optional_router'
```

#### Critical (required router failed) 
```
[app.main] ❌ CRITICAL: ROUTER_FAIL: {name} ({module}:{attr}) -> {exception_type}: {exception_message}
```

Example:
```
[app.main] ❌ CRITICAL: ROUTER_FAIL: heimdall (app.routers.heimdall:router) -> ImportError: Cannot import analyze_deal from app.services.heimdall_service
```

### Logging (log) Format

```python
log = logging.getLogger("valhalla.routers")
```

#### Success
```
log.info("ROUTER_OK: {name} ({module}:{attr}) prefix={prefix}")
```

#### Failure (optional)
```
log.warning("ROUTER_FAIL: {name} ({module}:{attr}) -> {exception}")
```

#### Failure (required - causes crash)
```
log.error("ROUTER_FAIL: {name} ({module}:{attr}) -> {exception}")
raise  # Application startup fails
```

## Startup Sequence

When `app.main` module loads, you will now see:

```
================================================================================
=== APP CREATED ===
================================================================================
[app.main] Registered router: system_selftest (app.routers.system_selftest:router) prefix=
[app.main] Registered router: governance_runbook (app.routers.runbook:router) prefix=/api
[app.main] Registered router: governance_policy (app.routers.governance_policy:router) prefix=/api
... [other governance routers] ...
[app.main] Registered router: heimdall (app.routers.heimdall:router) prefix=/api
[app.main] Registered router: audit (app.routers.audit:router) prefix=/api
[app.main] Registered router: operational_dashboard (app.routers.operational_dashboard:router) prefix=/api
... [optional routers] ...
================================================================================
=== ROUTER REGISTRY COMPLETE ===
================================================================================
```

## Failure Handling

### If Heimdall Import Fails
```
[app.main] ❌ CRITICAL: ROUTER_FAIL: heimdall (app.routers.heimdall:router) -> ImportError: cannot import name 'analyze_deal' from 'app.services.heimdall_service'
Traceback ...
... application startup FAILS ...
```

### If Optional Router Fails
```
[app.main] ⚠️  ROUTER_FAIL: some_optional_router (app.routers.some_optional_router:router) -> ImportError: No module named 'app.routers.some_optional_router'
... app continues loading ...
```

## Key Principle

**No silent failures on required routers.**

If `/api/heimdall/deals/{id}/analyze` is missing from the live app, it will be because:
1. The router module failed to import (logged + visible)
2. The router was never added to ROUTERS (code review catches this)
3. The prefix was misconfigured (visible in startup logs)

NOT because of a silent swallowing of errors.

## Related Files

- `app.core.router_registry.py` - Include function with logging
- `app.main.py` - ROUTERS list with required/optional flags
- Startup logs - Captured in application stdout during `uvicorn app.main:app --reload --port 4000`
