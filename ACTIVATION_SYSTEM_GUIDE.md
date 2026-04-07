# VALHALLA ACTIVATION SYSTEM - COMPREHENSIVE GUIDE
================================================

## Overview

The Activation System is the central control mechanism for launching dark modules in the VALHALLA ecosystem. It provides:

- **Condition-based activation** - Modules only activate when specific criteria are met
- **Dependency management** - Tracks module interdependencies 
- **Safety gates** - Manual approval points before activation
- **Audit logging** - Complete history of all activation events
- **Emergency controls** - Kill switches for immediate deactivation

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           MASTER ACTIVATION CONTROLLER                       │
│  (Orchestrates workflows, manages dependencies)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌─────────────────────┐     ┌─────────────────────┐
│ ACTIVATION          │     │ HTTP ENDPOINTS      │
│ CONDITIONS ENGINE   │     │ (API Routes)        │
├─────────────────────┤     ├─────────────────────┤
│ • Rules             │     │ POST /activate      │
│ • Metrics           │     │ GET /status         │
│ • Approval Gates    │     │ POST /enable-master │
│ • Status Checks     │     │ POST /emergency/*   │
└─────────────────────┘     └─────────────────────┘
```

---

## Components

### 1. Activation Conditions Engine (`activation_conditions.py`)

Manages the rules and conditions that must be met for a module to activate.

**Key Classes:**
- `ConditionType` - Enum of condition types (balance, time, volume, compliance, etc.)
- `ActivationRule` - Individual rule/condition
- `ActivationConditionEngine` - Manages all rules and gates

**Example:**
```python
from app.core_launch.activation_conditions import (
    ActivationConditionEngine,
    ActivationRule,
    ConditionType
)

engine = ActivationConditionEngine()

# Register a rule
rule = ActivationRule(
    name="min_balance",
    condition_type=ConditionType.MINIMUM_BALANCE,
    check_fn=lambda: engine.metrics.get("account_balance", 0) >= 10000,
    description="Account must have at least $10,000"
)

engine.register_rule("payment_processor", rule)

# Set metrics
engine.set_metric("account_balance", 50000)

# Check if module can activate
can_activate = engine.can_activate("payment_processor")  # True
```

### 2. Master Activation Controller (`master_activation_controller.py`)

Orchestrates the full activation workflow including dependency checking and state tracking.

**Key Classes:**
- `ActivationPhase` - Enum of workflow phases
- `ActivationStatus` - Enum of module states
- `ModuleActivationState` - Tracks state of a single module
- `ActivationController` - Main controller

**Workflow Phases:**
1. **INITIALIZATION** - Module registered
2. **CONDITION_CHECK** - Verify all activation conditions
3. **PRE_ACTIVATION** - Check dependencies and permissions
4. **ACTIVATION** - Actually activate the module
5. **POST_ACTIVATION** - Configure and initialize
6. **MONITORING** - Track health/status

**Example:**
```python
from app.core_launch.master_activation_controller import (
    ActivationController,
    register_module,
    full_activation
)

# Register modules
register_module("payment_processor")
register_module("banking_connector", ["payment_processor"])

# Run full activation workflow
success, message = await full_activation("banking_connector")

if success:
    print("✅ Banking connector activated!")
else:
    print(f"❌ Activation failed: {message}")
```

### 3. HTTP Endpoints (`routes/activation.py`)

FastAPI endpoints for managing activation via HTTP.

**Main Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/activation/enable-master` | Enable master activation |
| POST | `/api/v1/activation/disable-master` | Disable master activation |
| POST | `/api/v1/activation/activate/{module}` | Activate a module |
| GET | `/api/v1/activation/status` | Get current status |
| GET | `/api/v1/activation/status/{module}` | Get module status |
| POST | `/api/v1/activation/conditions/set-metric` | Set a metric |
| POST | `/api/v1/activation/conditions/approve-gate/{gate}` | Approve gate |
| POST | `/api/v1/activation/emergency/kill-switch` | Emergency deactivation |

---

## Usage Guide

### Starting the Activation System

```bash
# 1. Start the server
uvicorn app.main:app --reload --port 4000

# 2. Register modules (debug endpoint)
curl -X POST http://localhost:4000/api/v1/activation/debug/register-modules

# 3. Check status
curl http://localhost:4000/api/v1/activation/status
```

### Scenario: Activating the Payment Processor

```python
import requests

BASE_URL = "http://localhost:4000/api/v1/activation"

# Step 1: Set required metrics
requests.post(
    f"{BASE_URL}/conditions/set-metric",
    params={"metric_name": "account_balance", "value": 50000}
)

requests.post(
    f"{BASE_URL}/conditions/set-metric",
    params={"metric_name": "system_health", "value": True}
)

# Step 2: Approve necessary gates
requests.post(f"{BASE_URL}/conditions/approve-gate/payment_processor_approval")

# Step 3: Enable master activation
requests.post(f"{BASE_URL}/enable-master")

# Step 4: Activate module
response = requests.post(f"{BASE_URL}/activate/payment_processor")
result = response.json()

if result["status"] == "success":
    print("✅ Payment processor activated!")
    print(f"Activation count: {result['state']['activation_count']}")
else:
    print(f"❌ Failed: {result['message']}")
```

### Setting Activation Conditions

#### Minimum Balance Rule
```python
from app.core_launch.activation_conditions import set_metric

# Payment processor requires $10,000 minimum
set_metric("account_balance", 50000)  # Will pass (50k > 10k)
```

#### Approval Gates
```python
from app.core_launch.activation_conditions import approve_gate, reject_gate

# Require compliance approval
approve_gate("banking_compliance")

# Reject and require manual intervention
reject_gate("banking_compliance")
```

#### Custom Conditions
```python
from app.core_launch.activation_conditions import (
    ActivationConditionEngine,
    ActivationRule,
    ConditionType
)

engine = ActivationConditionEngine()

# Custom condition function
def check_api_credentials():
    return os.getenv("PLAID_API_KEY") is not None

rule = ActivationRule(
    "api_credentials",
    ConditionType.APPROVAL_GATE,
    check_api_credentials,
    "Plaid API credentials must be configured"
)

engine.register_rule("banking_connector", rule)
```

### Monitoring Activation Status

```python
import requests
import json

BASE_URL = "http://localhost:4000/api/v1/activation"

# Get full status
response = requests.get(f"{BASE_URL}/status")
status = response.json()

print(f"Master enabled: {status['master_enabled']}")
print(f"Active modules: {status['active_modules']}/{status['total_modules']}")

# Get specific module status
response = requests.get(f"{BASE_URL}/status/payment_processor")
module_status = response.json()

print(json.dumps(module_status, indent=2))
```

### Checking Activation Log

```python
import requests

BASE_URL = "http://localhost:4000/api/v1/activation"

# Get recent 10 activations
response = requests.get(f"{BASE_URL}/log?limit=10")
log = response.json()

for entry in log['entries']:
    timestamp = entry['timestamp']
    module = entry['module']
    result = entry['result']
    error = entry.get('error', 'N/A')
    
    print(f"{timestamp} | {module} | {result} | {error}")
```

---

## Activation Rules

### Default Rules by Module

#### payment_processor
- Minimum account balance: $10,000
- System health check: Must pass
- Approval gate: payment_processor_approval

#### banking_connector
- API credentials configured: Required
- Compliance approval: Required

#### heimdall_core (AI System)
- Active deals: Must have ≥ 5
- ML models: Must be trained
- Manual approval: heimdall_activation

#### property_cloning_engine
- Monthly revenue: Must exceed $100,000
- Leadership approval: Required

### Creating Custom Rules

```python
def create_custom_rules(engine):
    """Register custom activation rules."""
    
    from app.core_launch.activation_conditions import (
        ActivationRule,
        ConditionType
    )
    
    # Rule: API latency must be < 500ms
    rule1 = ActivationRule(
        "api_latency",
        ConditionType.SYSTEM_HEALTH,
        lambda: engine.metrics.get("api_latency_ms", 1000) < 500,
        "API latency must be < 500ms"
    )
    
    # Rule: Database connection pool sufficient
    rule2 = ActivationRule(
        "db_connections",
        ConditionType.SYSTEM_HEALTH,
        lambda: engine.metrics.get("available_connections", 0) > 10,
        "Must have >10 available DB connections"
    )
    
    engine.register_rule("my_module", rule1)
    engine.register_rule("my_module", rule2)
```

---

## Safety Features

### Master Enable/Disable

```python
# Must explicitly enable master to activate modules
requests.post("http://localhost:4000/api/v1/activation/enable-master")

# All activation attempts fail if master is disabled
```

### Dependency Management

```python
# Modules can have dependencies
# banking_connector depends on payment_processor

# If payment_processor fails to activate:
# - banking_connector activation will be blocked
# - Error: "Dependencies not met"
```

### Emergency Kill Switch

```python
# Immediately deactivate all modules
requests.post(
    "http://localhost:4000/api/v1/activation/emergency/kill-switch"
)

# Triggers:
# 1. Disable master activation
# 2. Call module-specific deactivation
# 3. Log emergency event
```

---

## Testing

### Running Tests

```bash
# Run all activation tests
pytest tests/test_activation_system.py -v

# Run specific test
pytest tests/test_activation_system.py::TestActivationEndpoints::test_enable_master -v

# Run with coverage
pytest tests/test_activation_system.py --cov=app.core_launch
```

### Test Coverage

The test suite covers:

- **Activation Conditions**
  - Rule creation and checking
  - Metric tracking
  - Approval gates
  - Status reporting

- **Activation Controller**
  - Module registration
  - Dependency checking
  - Condition verification
  - Activation workflow
  - Error handling

- **HTTP Endpoints**
  - Master enable/disable
  - Module activation
  - Status retrieval
  - Metric setting
  - Emergency controls

- **Integration**
  - Full activation workflow
  - Multi-module activation
  - Interdependency handling

---

## Deployment Checklist

- [ ] All modules registered with `register_module()`
- [ ] Default activation rules reviewed and configured
- [ ] Approval gates created for critical modules
- [ ] Test suite passing (100% coverage on core_launch)
- [ ] Error handling tested
- [ ] Emergency kill switch tested
- [ ] Audit logging verified
- [ ] Monitoring/alerting configured
- [ ] Documentation reviewed
- [ ] Team trained on activation process

---

## Troubleshooting

### Module Won't Activate

1. **Check conditions:**
   ```python
   curl http://localhost:4000/api/v1/activation/conditions
   ```

2. **Check module status:**
   ```python
   curl http://localhost:4000/api/v1/activation/status/module_name
   ```

3. **Check logs:**
   ```python
   curl http://localhost:4000/api/v1/activation/log?limit=50
   ```

### Emergency Scenarios

**Scenario: Module is stuck in ACTIVATING state**
- Use kill switch: `POST /emergency/kill-switch`
- Manually check module health
- Re-register if needed

**Scenario: Dependencies are circular**
- Check `activation_controller.dependencies`
- Break circular dependency (design issue)
- Re-register modules

**Scenario: Condition checks are hanging**
- Set timeout in condition check function
- Use threading with timeout wrapper
- Fallback to safe default (usually False)

---

## Security Considerations

1. **Master activation endpoint** - Should require admin authentication
2. **Emergency kill switch** - Should require multi-person approval
3. **Gate approval** - Should have audit trail
4. **Metrics setting** - Validate input, sanitize values
5. **API endpoints** - Use HTTPS in production
6. **Logging** - Store activation logs securely

---

## Performance Notes

- Condition checks are run synchronously - keep them fast
- Dependency checking is O(n) per module
- Status queries are O(1)
- Activation log grows unbounded - implement rotation
- Consider caching status for frequently-checked modules

---

## Future Enhancements

- [ ] Scheduled activation (cron-like)
- [ ] Conditional activation (if X then activate Y)
- [ ] Gradual rollout (activate X% of instances)
- [ ] Blue/green deployment support
- [ ] Automatic rollback on failure
- [ ] Machine learning for condition prediction
- [ ] GraphQL interface for activation
- [ ] Webhook notifications on state change

---

Generated: 2024
VALHALLA Activation System v1.0
