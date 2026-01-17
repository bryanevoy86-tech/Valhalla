#!/usr/bin/env python
"""
PHASE 3 GUARD ENFORCEMENT VERIFICATION
Test that safety constraints cannot be bypassed.
"""

import os
import sys
import subprocess

def test_scenario(name: str, env_vars: dict, should_pass: bool) -> bool:
    """Run SANDBOX_ACTIVATION with custom env vars and check result."""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    
    # Create a Python script that imports and runs the guard
    test_script = """
import os
import sys
sys.path.insert(0, '{valhalla_root}')

# Override env vars
{env_overrides}

from security.phase3_guard import (
    phase3_enabled,
    dry_run_enabled,
    outbound_disabled,
    assert_phase3_safety
)

print(f"Phase 3 enabled: {{phase3_enabled()}}")
print(f"DRY-RUN enabled: {{dry_run_enabled()}}")
print(f"Outbound disabled: {{outbound_disabled()}}")

try:
    assert_phase3_safety()
    print("✓ Guard check PASSED - system is safe")
    sys.exit(0)
except RuntimeError as e:
    print(f"✗ Guard check FAILED (INTENDED): {{e}}")
    sys.exit(1)
""".format(
        valhalla_root=os.getcwd(),
        env_overrides="\n".join(f"os.environ['{k}'] = '{v}'" for k, v in env_vars.items())
    )
    
    # Write temp test file
    with open("_temp_guard_test.py", "w") as f:
        f.write(test_script)
    
    # Run it
    result = subprocess.run(
        [sys.executable, "_temp_guard_test.py"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # Check result
    passed = (result.returncode == 0)
    expected = "PASSED" if should_pass else "FAILED"
    
    if (passed and should_pass) or (not passed and not should_pass):
        print(f"✅ TEST RESULT: {expected} (as expected)")
        return True
    else:
        print(f"❌ TEST RESULT: UNEXPECTED - expected {expected}")
        return False

def main():
    """Run all Phase 3 guard verification tests."""
    print("\n" + "="*70)
    print("PHASE 3 GUARD ENFORCEMENT VERIFICATION SUITE")
    print("Testing institutional-grade safety constraints")
    print("="*70)
    
    results = {}
    
    # Test 1: Normal operation (should pass)
    results["Normal Operation"] = test_scenario(
        "Normal Operation (DRY-RUN=1, DISABLE_OUTBOUND=1)",
        {
            "VALHALLA_ENV": "sandbox",
            "VALHALLA_PHASE": "3",
            "VALHALLA_REAL_DATA_INGEST": "1",
            "VALHALLA_DRY_RUN": "1",
            "VALHALLA_DISABLE_OUTBOUND": "1",
        },
        should_pass=True
    )
    
    # Test 2: DRY-RUN disabled (should fail)
    results["DRY-RUN Disabled"] = test_scenario(
        "ATTACK: Attempt to disable DRY-RUN (DRY-RUN=0)",
        {
            "VALHALLA_ENV": "sandbox",
            "VALHALLA_PHASE": "3",
            "VALHALLA_REAL_DATA_INGEST": "1",
            "VALHALLA_DRY_RUN": "0",
            "VALHALLA_DISABLE_OUTBOUND": "1",
        },
        should_pass=False
    )
    
    # Test 3: Outbound enabled (should fail)
    results["Outbound Enabled"] = test_scenario(
        "ATTACK: Attempt to enable outbound (DISABLE_OUTBOUND=0)",
        {
            "VALHALLA_ENV": "sandbox",
            "VALHALLA_PHASE": "3",
            "VALHALLA_REAL_DATA_INGEST": "1",
            "VALHALLA_DRY_RUN": "1",
            "VALHALLA_DISABLE_OUTBOUND": "0",
        },
        should_pass=False
    )
    
    # Test 4: Both constraints violated (should fail)
    results["Both Constraints Violated"] = test_scenario(
        "ATTACK: Disable both safeguards (DRY-RUN=0, DISABLE_OUTBOUND=0)",
        {
            "VALHALLA_ENV": "sandbox",
            "VALHALLA_PHASE": "3",
            "VALHALLA_REAL_DATA_INGEST": "1",
            "VALHALLA_DRY_RUN": "0",
            "VALHALLA_DISABLE_OUTBOUND": "0",
        },
        should_pass=False
    )
    
    # Clean up
    try:
        os.remove("_temp_guard_test.py")
    except:
        pass
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED - Guards are enforced")
        print("System is safe to proceed with Phase 3")
    else:
        print("❌ SOME TESTS FAILED - Guard system has issues")
        sys.exit(1)
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
