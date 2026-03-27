# STARTUP BLOCKERS TRACE

## Startup Command
```bash
cd d:\dev\services\api
$env:PYTHONPATH="d:\dev\services\api"
python -c "from app.main import app"
```

## Critical Blocker

### SQLAlchemy Table Redefinition Error

**Table: `deals`**

```
sqlalchemy.exc.InvalidRequestError: Table 'deals' is already defined for this MetaData instance.  
Specify 'extend_existing=True' to redefine options and columns on an existing Table object.
```

**Stack Trace (Abbreviated)**:
```
File "D:\dev\services/api\app\main.py", line 400, in <module>
    from app.deals.router import router as deals_router
  File "D:\dev\services/api\app\deals\router.py", line 12, in <module>
    from app.deals.models import Deal
  File "D:\dev\services/api\app\deals\models.py", line 36, in <module>
    class Deal(Base):
        ...
sqlalchemy.exc.InvalidRequestError: Table 'deals' is already defined for this MetaData instance.
```

**App State When Error Occurs**:
- Router registry successfully loaded and registered all required routers
- heimdall router registered ✅
- audit router registered ✅
- operational_dashboard router registered ✅
- App FAILED when trying to import `deals.router`
- Log shows: `[app.main] Skipping deals router: Table 'deals' is already defined...`

## What Was Seen Before the Error

The traceback shows successful registrations:
```
[app.main] Registered router: system_selftest
[app.main] Registered router: governance_runbook
...
[app.main] Registered router: heimdall prefix=/api
[app.main] Registered router: audit prefix=/api
[app.main] Registered router: operational_dashboard prefix=/api
...
=== ROUTER REGISTRY COMPLETE ===
```

Then later routers attempted to register:
```
[app.main] Floor control plane router registered
[app.main] Deal intake router registered
[app.main] Admin router registered
```

Then **CRASH** when trying to import deals router:
```
[app.main] Skipping deals router: Table 'deals' is already defined for this MetaData instance.
```

## Conflicting Table

| Table | First Definition | Second Definition | Status |
|-------|------------------|-------------------|--------|
| `deals` | [services/api/app/deals/models.py](services/api/app/deals/models.py) line 36 | Unknown (imported earlier) | DUPLICATE |

## Secondary Issues Noted (Non-Critical)

- `pack_sw` (life timeline) - Pydantic field annotation error
- `pack_sx` (emotional stability) - Pydantic field annotation error
- `pack_sy` (strategic decisions) - Pydantic field annotation error
- `pack_sz_ta_tb` - Module not found (3 missing routers)

## App Import Path That Triggers Error

1. main.py loads
2. ROUTERS registry loads and registers heimdall, audit, operational_dashboard ✅
3. Subsequent imports include deals router
4. deals router imports deals.models.Deal
5. Deal class definition tries to register `deals` table
6. **SQLAlchemy throws error: table already registered**
7. App fails to boot

## Next Action Required
Find where `deals` table is being imported/registered BEFORE line 400 of main.py.
