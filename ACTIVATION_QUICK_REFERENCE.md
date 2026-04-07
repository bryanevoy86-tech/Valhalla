# VALHALLA ACTIVATION SYSTEM - QUICK REFERENCE

## 🚀 Quick Start

```bash
# Start server
uvicorn app.main:app --reload --port 4000

# Register modules
curl -X POST http://localhost:4000/api/v1/activation/debug/register-modules

# Check status
curl http://localhost:4000/api/v1/activation/status
```

---

## 📋 Common Commands

### Enable/Disable Master

```bash
# Enable
curl -X POST http://localhost:4000/api/v1/activation/enable-master

# Disable
curl -X POST http://localhost:4000/api/v1/activation/disable-master
```

### Activate a Module

```bash
curl -X POST http://localhost:4000/api/v1/activation/activate/payment_processor
```

### Set Metrics

```bash
curl -X POST "http://localhost:4000/api/v1/activation/conditions/set-metric?metric_name=account_balance&value=50000"
```

### Approve/Reject Gates

```bash
# Approve
curl -X POST http://localhost:4000/api/v1/activation/conditions/approve-gate/payment_processor_approval

# Reject
curl -X POST http://localhost:4000/api/v1/activation/conditions/reject-gate/payment_processor_approval
```

### Check Status

```bash
# Full status
curl http://localhost:4000/api/v1/activation/status

# Module status
curl http://localhost:4000/api/v1/activation/status/payment_processor

# All conditions
curl http://localhost:4000/api/v1/activation/conditions

# Activation log
curl http://localhost:4000/api/v1/activation/log?limit=50
```

### Emergency

```bash
# Kill switch (deactivate all)
curl -X POST http://localhost:4000/api/v1/activation/emergency/kill-switch
```

---

## 🐍 Python Usage

### Activation Conditions

```python
from app.core_launch.activation_conditions import (
    set_metric,
    approve_gate,
    reject_gate,
    can_activate,
    get_activation_status,
    full_status
)

# Set metric
set_metric("account_balance", 50000)

# Approve gate
approve_gate("payment_processor_approval")

# Check status
if can_activate("payment_processor"):
    print("✅ Ready to activate")
else:
    print("❌ Not ready")
    status = get_activation_status("payment_processor")
    for condition in status["conditions"]:
        print(f"  {condition['name']}: {condition['last_result']}")
```

### Master Controller

```python
from app.core_launch.master_activation_controller import (
    register_module,
    full_activation,
    enable_master,
    disable_master,
    get_summary
)

# Register
register_module("payment_processor")
register_module("banking_connector", ["payment_processor"])

# Enable
enable_master()

# Activate
success, msg = await full_activation("payment_processor")

# Check summary
summary = get_summary()
print(f"Active: {summary['active_modules']}/{summary['total_modules']}")
```

### Custom Rules

```python
from app.core_launch.activation_conditions import (
    ActivationConditionEngine,
    ActivationRule,
    ConditionType
)

engine = ActivationConditionEngine()

rule = ActivationRule(
    "custom_check",
    ConditionType.SYSTEM_HEALTH,
    lambda: check_something(),  # Your check function
    "Description of what's being checked"
)

engine.register_rule("my_module", rule)
```

---

## 📊 Module Dependencies

```
payment_processor
    ↓
banking_connector
    ↓
heimdall_core (AI)
    ↓
property_cloning_engine
```

Modules only activate if all dependencies are ACTIVE.

---

## ✅ Activation Requirements by Module

### payment_processor
- [ ] account_balance ≥ $10,000
- [ ] system_health = True
- [ ] payment_processor_approval = approved

### banking_connector
- [ ] Depends on: payment_processor (ACTIVE)
- [ ] banking_credentials = approved
- [ ] banking_compliance = approved

### heimdall_core
- [ ] Depends on: banking_connector (ACTIVE)
- [ ] active_deals ≥ 5
- [ ] heimdall_models = approved
- [ ] heimdall_activation = approved

### property_cloning_engine
- [ ] Depends on: heimdall_core (ACTIVE)
- [ ] monthly_revenue ≥ $100,000
- [ ] scaling_approval = approved

---

## 🔄 Activation Workflow

```
1. Register modules
   register_module("payment_processor")

2. Set metrics
   set_metric("account_balance", 50000)

3. Approve gates
   approve_gate("payment_processor_approval")

4. Enable master
   enable_master()

5. Activate
   await full_activation("payment_processor")

6. Monitor
   get_summary()
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/test_activation_system.py -v

# Run specific test class
pytest tests/test_activation_system.py::TestActivationEndpoints -v

# Run with coverage
pytest tests/test_activation_system.py --cov=app.core_launch --cov-report=html
```

---

## 📈 States & Phases

### Module Status
- PENDING → CHECKING → READY → ACTIVATING → ACTIVE
- (or) → FAILED, BLOCKED

### Activation Phases
1. INITIALIZATION - Module registered
2. CONDITION_CHECK - Verify conditions
3. PRE_ACTIVATION - Check dependencies
4. ACTIVATION - Activate
5. POST_ACTIVATION - Configure
6. MONITORING - Track health

---

## 🚨 Emergency

| Situation | Action |
|-----------|--------|
| Module stuck | Kill switch: `POST /emergency/kill-switch` |
| Circular deps | Redesign dependencies |
| Condition error | Check logs: `GET /log` |
| Master broken | `POST /disable-master` then investigate |

---

## 📝 Logging & Audit

```bash
# View activation log
curl http://localhost:4000/api/v1/activation/log?limit=50

# Sample entry:
# {
#   "timestamp": "2024-01-15T10:30:45.123Z",
#   "module": "payment_processor", 
#   "result": "success",
#   "error": null
# }
```

---

## 🔍 Debugging Tips

### Module won't activate?

```python
# 1. Check conditions
status = get_activation_status("module_name")
for cond in status["conditions"]:
    print(f"{cond['name']}: {cond['last_result']}")

# 2. Check dependencies
if not check_dependencies("module_name"):
    print("Missing dependencies!")

# 3. Check metrics
from app.core_launch.activation_conditions import _condition_engine
print(_condition_engine.metrics)

# 4. Check gates
print(_condition_engine.approvals)
```

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| `app/core_launch/activation_conditions.py` | Rules & conditions engine |
| `app/core_launch/master_activation_controller.py` | Orchestration logic |
| `app/routes/activation.py` | HTTP endpoints |
| `tests/test_activation_system.py` | Test suite |
| `ACTIVATION_SYSTEM_GUIDE.md` | Full documentation |

---

## 🎯 Example: Complete Flow

```python
# Step-by-step activation of payment processor

from app.core_launch.activation_conditions import (
    set_metric, approve_gate, full_status
)
from app.core_launch.master_activation_controller import (
    register_module, enable_master, full_activation
)

# 1. Register
register_module("payment_processor")

# 2. Set metrics
set_metric("account_balance", 50000)
set_metric("system_health", True)

# 3. Approve gates
approve_gate("payment_processor_approval")

# 4. Enable master
enable_master()

# 5. Activate
success, msg = await full_activation("payment_processor")
print(f"✅ Activation: {success}")

# 6. Verify
summary = full_status()
print(f"Module status: {summary['modules']['payment_processor']}")
```

---

**For detailed information, see: `ACTIVATION_SYSTEM_GUIDE.md`**
