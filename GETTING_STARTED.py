#!/usr/bin/env python3
"""
VALHALLA ACTIVATION SYSTEM - GETTING STARTED WORKBOOK
======================================================

Copy-paste examples to get up and running quickly.
"""

# ================================================
# EXAMPLE 1: Start Server and Check Status
# ================================================

"""
Terminal 1: Start API Server
$ uvicorn app.main:app --reload --port 4000

Terminal 2: Check if running
$ curl http://localhost:4000/api/v1/activation/status
"""

# ================================================
# EXAMPLE 2: Register Modules (Python)
# ================================================

import asyncio
from app.core_launch.master_activation_controller import register_module, get_summary

# Register the 4 default modules
register_module("payment_processor")
register_module("banking_connector", ["payment_processor"])
register_module("heimdall_core", ["banking_connector"])
register_module("property_cloning_engine", ["heimdall_core"])

print("✅ Modules registered")


# ================================================
# EXAMPLE 3: Set Up Activation (Payment Processor)
# ================================================

from app.core_launch.activation_conditions import (
    set_metric,
    approve_gate,
    full_status
)

# Step 1: Set metrics
set_metric("account_balance", 50000)  # Account has $50k
set_metric("system_health", True)      # System is healthy

# Step 2: Approve required gates
approve_gate("payment_processor_approval")

# Step 3: Check conditions satisfied
status = full_status()
print(status['modules']['payment_processor'])


# ================================================
# EXAMPLE 4: Activate a Module (Python)
# ================================================

from app.core_launch.master_activation_controller import (
    enable_master,
    full_activation as activate_module
)

# Step 1: Enable master
enable_master()
print("✅ Master enabled")

# Step 2: Activate
async def activate():
    success, msg = await activate_module("payment_processor")
    if success:
        print("✅ Payment processor ACTIVATED!")
    else:
        print(f"❌ Failed: {msg}")

asyncio.run(activate())


# ================================================
# EXAMPLE 5: Check Status (curl)
# ================================================

"""
# Full status
curl http://localhost:4000/api/v1/activation/status

# Specific module
curl http://localhost:4000/api/v1/activation/status/payment_processor

# All conditions
curl http://localhost:4000/api/v1/activation/conditions

# Activation log
curl http://localhost:4000/api/v1/activation/log?limit=10
"""


# ================================================
# EXAMPLE 6: Set Metric & Approve Gate (curl)
# ================================================

"""
# Set a metric
curl -X POST \\
  "http://localhost:4000/api/v1/activation/conditions/set-metric?metric_name=account_balance&value=75000"

# Approve a gate
curl -X POST \\
  http://localhost:4000/api/v1/activation/conditions/approve-gate/payment_processor_approval

# Reject a gate
curl -X POST \\
  http://localhost:4000/api/v1/activation/conditions/reject-gate/payment_processor_approval
"""


# ================================================
# EXAMPLE 7: Full Activation Flow (Python)
# ================================================

async def full_activation_flow():
    """Complete activation flow example."""
    from app.core_launch.activation_conditions import (
        set_metric, approve_gate, get_activation_status
    )
    from app.core_launch.master_activation_controller import (
        register_module, enable_master, full_activation, get_summary
    )
    from unittest.mock import patch
    
    print("\n" + "="*60)
    print("FULL ACTIVATION FLOW EXAMPLE")
    print("="*60)
    
    # 1. Register module
    print("\n[1] Register module")
    register_module("payment_processor")
    print("    ✅ payment_processor registered")
    
    # 2. Set metrics
    print("\n[2] Set activation metrics")
    set_metric("account_balance", 50000)
    set_metric("system_health", True)
    print("    ✅ Metrics set")
    
    # 3. Approve gates
    print("\n[3] Approve gates")
    approve_gate("payment_processor_approval")
    print("    ✅ payment_processor_approval approved")
    
    # 4. Enable master
    print("\n[4] Enable master activation")
    enable_master()
    print("    ✅ Master enabled")
    
    # 5. Check conditions
    print("\n[5] Check conditions")
    status = get_activation_status("payment_processor")
    conditions = status["conditions"]
    for cond in conditions:
        result = "✅" if cond["last_result"] else "❌"
        print(f"    {result} {cond['name']}: {cond['last_result']}")
    
    # 6. Activate
    print("\n[6] Activate module")
    with patch("app.core_launch.master_activation_controller.can_activate", return_value=True):
        success, msg = await full_activation("payment_processor")
    
    if success:
        print("    ✅ ACTIVATED!")
    else:
        print(f"    ❌ Failed: {msg}")
    
    # 7. Verify
    print("\n[7] Verify")
    summary = get_summary()
    print(f"    Active modules: {summary['active_modules']}/{summary['total_modules']}")
    print("\n" + "="*60)

# Run the full flow
# asyncio.run(full_activation_flow())


# ================================================
# EXAMPLE 8: Check Dependencies
# ================================================

from app.core_launch.master_activation_controller import ActivationController

controller = ActivationController()

# Register with dependencies
controller.register_module("payment_processor")
controller.register_module("banking_connector", ["payment_processor"])

# Check dependency - should fail
deps_met = controller.check_dependencies("banking_connector")
print(f"Dependencies met (before): {deps_met}")  # False

# Mock activating payment_processor
from app.core_launch.master_activation_controller import ActivationStatus
controller.modules["payment_processor"].status = ActivationStatus.ACTIVE

# Check dependency - should pass
deps_met = controller.check_dependencies("banking_connector")
print(f"Dependencies met (after): {deps_met}")  # True


# ================================================
# EXAMPLE 9: Error Handling
# ================================================

async def handle_activation_error():
    """Example of handling activation errors."""
    from app.core_launch.master_activation_controller import (
        register_module, full_activation
    )
    
    register_module("test_module")
    
    try:
        success, msg = await full_activation("test_module")
        if not success:
            print(f"⚠️  Activation failed: {msg}")
            # Take corrective action
    except Exception as e:
        print(f"❌ Error: {e}")
        # Handle error


# ================================================
# EXAMPLE 10: Custom Activation Rule
# ================================================

from app.core_launch.activation_conditions import (
    ActivationConditionEngine,
    ActivationRule,
    ConditionType
)

# Create custom rule
def my_custom_check():
    """Custom business logic check."""
    # e.g., check external service
    return True

custom_rule = ActivationRule(
    "my_custom_check",
    ConditionType.METRIC_THRESHOLD,
    my_custom_check,
    "My custom business requirement"
)

# Register it
from app.core_launch.activation_conditions import _condition_engine
_condition_engine.register_rule("payment_processor", custom_rule)

print("✅ Custom rule registered")


# ================================================
# EXAMPLE 11: Emergency Scenarios
# ================================================

"""
# Emergency kill switch (deactivate everything)
curl -X POST http://localhost:4000/api/v1/activation/emergency/kill-switch

# Disable master (blocks new activations)
curl -X POST http://localhost:4000/api/v1/activation/disable-master

# Check what went wrong
curl http://localhost:4000/api/v1/activation/log?limit=50
"""


# ================================================
# EXAMPLE 12: Running Tests
# ================================================

"""
# Run all tests
$ pytest tests/test_activation_system.py -v

# Run specific test class
$ pytest tests/test_activation_system.py::TestActivationEndpoints -v

# Run with coverage
$ pytest tests/test_activation_system.py --cov=app.core_launch

# Run specific test
$ pytest tests/test_activation_system.py::test_module_registration -v

# Run interactive test script
$ python activation_test.py
"""


# ================================================
# EXAMPLE 13: Monitoring Commands
# ================================================

"""
# Get full status
curl http://localhost:4000/api/v1/activation/status | jq .

# Get one module status
curl http://localhost:4000/api/v1/activation/status/payment_processor | jq .

# Get recent activations
curl http://localhost:4000/api/v1/activation/log?limit=20 | jq '.entries'

# Watch status in real-time
watch -n 1 'curl -s http://localhost:4000/api/v1/activation/status | jq .total_active'
"""


# ================================================
# EXAMPLE 14: Batch Operations (Activate Multiple)
# ================================================

async def batch_activate():
    """Activate multiple modules in sequence."""
    from app.core_launch.master_activation_controller import (
        enable_master, full_activation
    )
    
    modules = [
        "payment_processor",
        "banking_connector",
        "heimdall_core",
        "property_cloning_engine"
    ]
    
    enable_master()
    
    for module in modules:
        print(f"\n🚀 Activating {module}...")
        success, msg = await full_activation(module)
        if success:
            print(f"✅ {module} activated")
        else:
            print(f"❌ {module} failed: {msg}")
            break  # Stop on first failure


# ================================================
# EXAMPLE 15: Status Dashboard (Python)
# ================================================

def show_activation_dashboard():
    """Display activation status in a nice format."""
    from app.core_launch.master_activation_controller import get_summary
    
    summary = get_summary()
    
    print("\n" + "="*60)
    print("VALHALLA ACTIVATION DASHBOARD")
    print("="*60)
    
    print(f"\nMaster Enabled: {'✅ Yes' if summary['master_enabled'] else '❌ No'}")
    print(f"Active Modules: {summary['active_modules']}/{summary['total_modules']}")
    
    print("\nModule Status:")
    print("-" * 60)
    
    for name, module in summary['modules'].items():
        status_icon = {
            "active": "✅",
            "pending": "⏳",
            "failed": "❌",
            "blocked": "🔒",
        }.get(module['status'], "❓")
        
        print(f"{status_icon} {name:30} {module['status']:12} " +
              f"(count: {module['activation_count']})")
    
    print("\n" + "="*60)


# Run dashboard
# show_activation_dashboard()


# ================================================
# QUICK REFERENCE: API Endpoints
# ================================================

"""
POST   /api/v1/activation/enable-master
POST   /api/v1/activation/disable-master
POST   /api/v1/activation/activate/{module_name}
GET    /api/v1/activation/status
GET    /api/v1/activation/status/{module_name}
GET    /api/v1/activation/conditions
POST   /api/v1/activation/conditions/set-metric?metric_name=X&value=Y
POST   /api/v1/activation/conditions/approve-gate/{gate_name}
POST   /api/v1/activation/conditions/reject-gate/{gate_name}
GET    /api/v1/activation/log?limit=50
POST   /api/v1/activation/emergency/kill-switch
POST   /api/v1/activation/debug/register-modules
"""


# ================================================
# Quick Start: Copy-Paste Workflow
# ================================================

"""
1. Start server:
   $ uvicorn app.main:app --reload --port 4000

2. Register modules:
   $ curl -X POST http://localhost:4000/api/v1/activation/debug/register-modules

3. Set metrics:
   $ curl -X POST "http://localhost:4000/api/v1/activation/conditions/set-metric?metric_name=account_balance&value=50000"

4. Approve gates:
   $ curl -X POST http://localhost:4000/api/v1/activation/conditions/approve-gate/payment_processor_approval

5. Enable master:
   $ curl -X POST http://localhost:4000/api/v1/activation/enable-master

6. Activate module:
   $ curl -X POST http://localhost:4000/api/v1/activation/activate/payment_processor

7. Check status:
   $ curl http://localhost:4000/api/v1/activation/status
"""

print("\n✅ VALHALLA ACTIVATION SYSTEM WORKBOOK LOADED")
print("\nCopy-paste any example above to get started!")
print("\nFor more info:")
print("  - Full guide: ACTIVATION_SYSTEM_GUIDE.md")
print("  - Quick ref:  ACTIVATION_QUICK_REFERENCE.md")
print("  - Deploy:     ACTIVATION_DEPLOYMENT_GUIDE.md")
print("  - Tests:      pytest tests/test_activation_system.py")
print("  - Interactive: python activation_test.py")
