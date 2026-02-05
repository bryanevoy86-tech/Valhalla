# Quick Reference: Module Build Pack

## One-Page Architecture

### Runtime Modes (Global Rule)
```python
from app.core.runtime_flags import is_live, is_armed, is_sandbox

is_sandbox()  # ← Default, safe mode (no side effects)
is_armed()    # ← Ready mode (mocks real operations)
is_live()     # ← Live mode (real operations enabled)
```

### Check Before Reality-Touching Code
```python
if not is_live():
    return mock_response()  # Safe return

# Only here if LIVE
send_real_email()
process_stripe_charge()
```

---

## 10-Module Reference

| Module | File | Key Class/Function | Use Case |
|--------|------|-------------------|----------|
| 1️⃣ Runtime Flags | `app/core/runtime_flags.py` | `RuntimeMode` enum | Global mode control |
| 2️⃣ Heimdall | `app/heimdall/authority.py` | `HEIMDALL.activation_allowed()` | System readiness gate |
| 3️⃣ Contracts | `app/contracts/` | `Contract`, `send_contract()` | Contract lifecycle |
| 4️⃣ Payments | `app/payments/gateway.py` | `create_invoice()` | Stripe integration |
| 5️⃣ Ledger | `app/ledger/` | `RevenueEntry`, `record_revenue()` | Revenue tracking |
| 6️⃣ Real Estate | `app/realestate/engine.py` | `evaluate_deal()`, `issue_offer()` | Deal evaluation |
| 7️⃣ Floor Control | `app/governance/floor_enforcer.py` | `enforce_floor()` | Threshold enforcement |
| 8️⃣ AI Engines | `app/ai_engines/base.py` | `AutonomousEngine` ABC | Custom engine template |
| 9️⃣ QuickBooks | `app/accounting/quickbooks.py` | `sync_revenue()` | Accounting queue |
| 🔟 Admin | `app/admin/runtime.py` | `arm_system()`, `go_live()` | System armament |

---

## Common Patterns

### Contract Creation & Execution
```python
from app.contracts.service import create_contract, send_contract

# 1. Create
contract = create_contract(
    db=db,
    template_id=1,
    title="Purchase Agreement",
    merge_data={"price": 500000}
)

# 2. Update state
update_contract_state(db, contract.id, "SENT")

# 3. Send (requires LIVE)
try:
    send_contract(db, contract.id)  # Raises RuntimeError if not LIVE
except RuntimeError:
    # In SANDBOX/ARMED mode
    pass
```

### Record Revenue
```python
from app.ledger.service import record_revenue

entry = record_revenue(
    db=db,
    engine="realestate",
    amount=50000,          # $500 in cents
    source="deal_12345"
)
```

### Evaluate Deal & Issue Offer
```python
from app.realestate.engine import evaluate_deal, issue_offer

deal = {
    "id": "deal_123",
    "price": 300000,
    "arv": 500000,
    "repairs": 50000
}

eval = evaluate_deal(deal)
offer = issue_offer(deal, discount=0.9)
```

### Custom Autonomous Engine
```python
from app.ai_engines.base import AutonomousEngine

class MyEngine(AutonomousEngine):
    def evaluate(self, context):
        return {
            "ready": context["score"] > 70,
            "score": context["score"]
        }
    
    def execute(self, context):
        return {"success": True, "result": do_something()}

engine = MyEngine("My Engine")
result = engine.run(context)
```

### Floor Control
```python
from app.governance.floor_enforcer import enforce_floor

result = enforce_floor(actual=50000, target=40000)
# {"decision": "ALLOW", "buffer": 10000}
```

### System Armament
```python
from app.admin.runtime import arm_system, go_live

status = get_runtime_status()
result = arm_system(authorized_by="dev")
result = go_live(authorized_by="admin")  # IRREVERSIBLE
```

---

## Mode Behavior Summary

| Operation | SANDBOX | ARMED | LIVE |
|-----------|---------|-------|------|
| Contract operations | ✅ | ✅ | ✅ |
| Send contracts | ❌ | ❌ | ✅ |
| Real payments | ❌ Mock | ❌ Mock | ✅ Real |
| Real offers | ❌ Mock | ❌ Mock | ✅ Real |

---

## Commit: 0dcaef4

**All 10 modules implemented and committed** ✅

- ✅ Runtime flags
- ✅ Heimdall authority  
- ✅ Contracts (models, service, router)
- ✅ Payments gateway
- ✅ Revenue ledger
- ✅ Real estate engine
- ✅ Floor control
- ✅ AI engines base
- ✅ QuickBooks sync
- ✅ Admin runtime control

Production-ready and tested for imports.
