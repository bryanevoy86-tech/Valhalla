# Engine Guards (Locked Canon)

## Key Rule
SANDBOX blocks **real-world effects**, not real-world data.

Real-world effects include:
- outreach (sms/email/calls)
- sending deals to buyers
- contract generation/signing workflows
- any money movement
- broker execution (trading)

SANDBOX is allowed to:
- ingest real data
- compute scores
- generate advisory recommendations
- generate internal tasks
- log outputs and decisions
- simulate actions (preview only)

Engine state transitions are governed only by Heimdall:
DISABLED -> DORMANT -> SANDBOX -> ACTIVE
No skipping.

IMPORTANT: one small wiring step in app/main.py

You must include the new router so the API exposes it.

Find where routers are included in app/main.py and add:

```python
from app.routers.engine_admin import router as engine_admin_router
app.include_router(engine_admin_router)
```

(Place it near your other governance/system routers.)
