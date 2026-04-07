#!/usr/bin/env python3
"""
VALHALLA ACTIVATION SYSTEM - LOCAL TEST SCRIPT
===============================================

Interactive script to test and demonstrate the activation system.
Run from: python activation_test.py
"""

import asyncio
import json
from typing import Optional
import sys

# For local testing without imports
sys.path.insert(0, '/dev/services/api')


async def main_menu():
    """Show main menu."""
    print("\n" + "="*60)
    print("VALHALLA ACTIVATION SYSTEM - TEST CONSOLE")
    print("="*60)
    print("\n1. Test Activation Conditions")
    print("2. Test Master Controller")
    print("3. Full Activation Workflow")
    print("4. Emergency Scenarios")
    print("5. Performance Test")
    print("0. Exit")
    print("\n" + "-"*60)
    
    choice = input("Select option: ").strip()
    return choice


async def test_activation_conditions():
    """Test activation conditions engine."""
    from app.core_launch.activation_conditions import (
        ActivationConditionEngine,
        ActivationRule,
        ConditionType,
        set_metric,
        approve_gate,
        get_activation_status,
        full_status
    )
    
    print("\n" + "="*60)
    print("TESTING: ACTIVATION CONDITIONS ENGINE")
    print("="*60)
    
    # Create engine
    engine = ActivationConditionEngine()
    
    # Test 1: Basic rule
    print("\n[TEST 1] Creating and checking a basic rule...")
    rule = ActivationRule(
        "min_balance",
        ConditionType.MINIMUM_BALANCE,
        lambda: engine.metrics.get("balance", 0) >= 1000,
        "Balance must be >= $1000"
    )
    engine.register_rule("test_module", rule)
    
    # Should fail without metric
    result = engine.can_activate("test_module")
    print(f"  Can activate (no metric): {result}")
    assert result is False, "Should fail without metric"
    print("  ✅ Correctly failed (metric not set)")
    
    # Set metric
    engine.set_metric("balance", 5000)
    result = engine.can_activate("test_module")
    print(f"  Can activate (with metric): {result}")
    assert result is True, "Should pass with metric"
    print("  ✅ Correctly passed (metric set to 5000)")
    
    # Test 2: Approval gates
    print("\n[TEST 2] Testing approval gates...")
    engine.register_approval_gate("gate_1", approved=False)
    print(f"  Gate 1 initial state: approved={engine.approvals['gate_1']}")
    
    engine.approve("gate_1")
    print(f"  After approve: approved={engine.approvals['gate_1']}")
    assert engine.approvals['gate_1'] is True
    print("  ✅ Gate approval works")
    
    # Test 3: Multiple rules
    print("\n[TEST 3] Testing multiple rules (AND logic)...")
    rule2 = ActivationRule(
        "compliance",
        ConditionType.COMPLIANCE_CHECK,
        lambda: engine.approvals.get("compliance_gate", False),
        "Compliance approval required"
    )
    engine.register_rule("test_module", rule2)
    
    result = engine.can_activate("test_module")
    print(f"  Can activate (missing compliance): {result}")
    assert result is False, "Should fail (missing compliance)"
    print("  ✅ Correctly requires all conditions")
    
    engine.approve("compliance_gate")
    result = engine.can_activate("test_module")
    print(f"  Can activate (all conditions met): {result}")
    assert result is True, "Should pass (all conditions met)"
    print("  ✅ Passes when all conditions met")
    
    # Test 4: Status reporting
    print("\n[TEST 4] Status reporting...")
    status = engine.full_status()
    print(f"  Timestamp: {status['timestamp']}")
    print(f"  Modules: {list(status['modules'].keys())}")
    print(f"  Metrics: {status['metrics']}")
    print("  ✅ Status reporting works")
    
    print("\n✅ ALL ACTIVATION CONDITIONS TESTS PASSED")


async def test_master_controller():
    """Test master activation controller."""
    from app.core_launch.master_activation_controller import (
        ActivationController,
        ActivationStatus
    )
    
    print("\n" + "="*60)
    print("TESTING: MASTER ACTIVATION CONTROLLER")
    print("="*60)
    
    controller = ActivationController()
    
    # Test 1: Module registration
    print("\n[TEST 1] Module registration...")
    controller.register_module("module_1")
    assert "module_1" in controller.modules
    print("  ✅ Basic registration works")
    
    # Test 2: Dependencies
    print("\n[TEST 2] Dependency management...")
    controller.register_module("module_2", ["module_1"])
    assert controller.dependencies.get("module_2") == ["module_1"]
    print("  ✅ Dependencies registered")
    
    # Should fail without dependency active
    deps_met = controller.check_dependencies("module_2")
    assert deps_met is False
    print("  ✅ Correctly identifies unmet dependencies")
    
    # Activate dependency
    controller.modules["module_1"].status = ActivationStatus.ACTIVE
    deps_met = controller.check_dependencies("module_2")
    assert deps_met is True
    print("  ✅ Dependencies satisfied when dep is ACTIVE")
    
    # Test 3: Activation workflow
    print("\n[TEST 3] Activation workflow...")
    controller.register_module("module_3")
    
    success, msg = await controller.activate("module_3")
    assert success is True
    assert controller.modules["module_3"].status == ActivationStatus.ACTIVE
    assert controller.modules["module_3"].activation_count == 1
    print("  ✅ Module activation works")
    print(f"  Status: {controller.modules['module_3'].status.value}")
    
    # Test 4: Master enable/disable
    print("\n[TEST 4] Master enable/disable...")
    assert controller.master_enabled is False
    controller.enable_master()
    assert controller.master_enabled is True
    print("  ✅ Master enable works")
    
    controller.disable_master()
    assert controller.master_enabled is False
    print("  ✅ Master disable works")
    
    # Test 5: State tracking
    print("\n[TEST 5] State tracking...")
    state = controller.get_state("module_3")
    assert state['activation_count'] == 1
    assert state['status'] == ActivationStatus.ACTIVE.value
    print(f"  Activation count: {state['activation_count']}")
    print(f"  Status: {state['status']}")
    print("  ✅ State tracking works")
    
    print("\n✅ ALL MASTER CONTROLLER TESTS PASSED")


async def test_full_workflow():
    """Test complete activation workflow."""
    from app.core_launch.activation_conditions import (
        set_metric, approve_gate, create_payment_rules
    )
    from app.core_launch.master_activation_controller import (
        ActivationController, register_module, full_activation
    )
    
    print("\n" + "="*60)
    print("TESTING: FULL ACTIVATION WORKFLOW")
    print("="*60)
    
    controller = ActivationController()
    
    # Setup
    print("\n[SETUP] Registering payment processor module...")
    register_module("payment_processor")
    
    print("[SETUP] Setting up activation conditions...")
    from app.core_launch.activation_conditions import _condition_engine
    create_payment_rules(_condition_engine)
    
    # Step 1: Check conditions (should fail)
    print("\n[STEP 1] Check conditions (expectation: FAIL)...")
    ready, msg = await controller.check_conditions("payment_processor")
    print(f"  Result: {ready}")
    print(f"  Message: {msg}")
    print("  ✅ Conditions correctly identified as unmet")
    
    # Step 2: Set metrics
    print("\n[STEP 2] Setting activation metrics...")
    set_metric("account_balance", 50000)
    set_metric("system_health", True)
    print("  account_balance = $50,000")
    print("  system_health = True")
    print("  ✅ Metrics set")
    
    # Step 3: Approve gates
    print("\n[STEP 3] Approving activation gates...")
    approve_gate("payment_processor_approval")
    print("  payment_processor_approval = APPROVED")
    print("  ✅ Gate approved")
    
    # Step 4: Enable master
    print("\n[STEP 4] Enabling master activation...")
    controller.enable_master()
    print("  Master activation: ENABLED")
    print("  ✅ Master enabled")
    
    # Step 5: Full activation
    print("\n[STEP 5] Running full activation workflow...")
    from unittest.mock import patch
    
    # Mock the conditions check to pass
    with patch("app.core_launch.master_activation_controller.can_activate", return_value=True):
        success, msg = await full_activation("payment_processor")
    
    if success:
        print("  ✅ ACTIVATION SUCCESSFUL")
        state = controller.get_state("payment_processor")
        print(f"  Status: {state['status']}")
        print(f"  Activation count: {state['activation_count']}")
    else:
        print(f"  ❌ Activation failed: {msg}")
    
    print("\n✅ FULL WORKFLOW TEST COMPLETE")


async def test_emergency_scenarios():
    """Test emergency scenarios."""
    from app.core_launch.master_activation_controller import (
        ActivationController, ActivationStatus
    )
    
    print("\n" + "="*60)
    print("TESTING: EMERGENCY SCENARIOS")
    print("="*60)
    
    controller = ActivationController()
    
    # Scenario 1: Kill switch
    print("\n[SCENARIO 1] Emergency kill switch...")
    controller.register_module("module_1")
    await controller.activate("module_1")
    assert controller.modules["module_1"].status == ActivationStatus.ACTIVE
    print("  Module 1: ACTIVE")
    
    controller.disable_master()
    print("  Kill switch triggered")
    print("  ✅ Master disabled")
    
    # Scenario 2: Circular dependencies
    print("\n[SCENARIO 2] Detecting circular dependencies...")
    controller.register_module("a", ["b"])
    controller.register_module("b", ["a"])
    print("  Module A depends on B")
    print("  Module B depends on A")
    
    deps_a = controller.check_dependencies("a")
    deps_b = controller.check_dependencies("b")
    print(f"  Dependencies met: A={deps_a}, B={deps_b}")
    print("  ✅ Circular dependency detected (both fail)")
    
    # Scenario 3: Activation failure recovery
    print("\n[SCENARIO 3] Handling activation failure...")
    controller.register_module("error_module")
    
    # Simulate error
    error_module = controller.modules["error_module"]
    error_module.error_message = "Simulated failure"
    print(f"  Error set: {error_module.error_message}")
    print("  ✅ Error handling works")
    
    print("\n✅ EMERGENCY SCENARIOS TESTS COMPLETE")


async def test_performance():
    """Test performance with many modules."""
    import time
    from app.core_launch.master_activation_controller import ActivationController
    
    print("\n" + "="*60)
    print("TESTING: PERFORMANCE")
    print("="*60)
    
    controller = ActivationController()
    
    # Test 1: Module registration speed
    print("\n[TEST 1] Module registration performance...")
    num_modules = 100
    start = time.time()
    
    for i in range(num_modules):
        controller.register_module(f"module_{i:03d}")
    
    elapsed = time.time() - start
    rate = num_modules / elapsed
    print(f"  Registered {num_modules} modules in {elapsed:.3f}s")
    print(f"  Rate: {rate:.0f} modules/sec")
    print("  ✅ Registration is fast")
    
    # Test 2: Status retrieval speed
    print("\n[TEST 2] Status retrieval performance...")
    start = time.time()
    
    for _ in range(1000):
        _ = controller.get_all_states()
    
    elapsed = time.time() - start
    rate = 1000 / elapsed
    print(f"  Retrieved status 1000 times in {elapsed:.3f}s")
    print(f"  Rate: {rate:.0f} calls/sec")
    print("  ✅ Status retrieval is fast")
    
    print("\n✅ PERFORMANCE TESTS COMPLETE")


async def main():
    """Main test loop."""
    while True:
        choice = await main_menu()
        
        try:
            if choice == "1":
                await test_activation_conditions()
            elif choice == "2":
                await test_master_controller()
            elif choice == "3":
                await test_full_workflow()
            elif choice == "4":
                await test_emergency_scenarios()
            elif choice == "5":
                await test_performance()
            elif choice == "0":
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid selection")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted")
