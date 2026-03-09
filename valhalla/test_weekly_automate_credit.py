#!/usr/bin/env python
"""
Comprehensive smoke tests for PACK 4-6 deployment:
- P-WEEKLY-1: Weekly System Check (nothing dropped audit)
- P-AUTOMATE-1: Rules/Triggers automation engine
- P-CREDIT-1: Business Credit Engine
"""

import sys
import json
from datetime import datetime, date, timedelta

tests_passed = 0
tests_failed = 0


def test(name: str, condition: bool, detail: str = ""):
    global tests_passed, tests_failed
    if condition:
        print(f"  ✓ {name}")
        if detail:
            print(f"    {detail}")
        tests_passed += 1
    else:
        print(f"  ✗ {name}")
        if detail:
            print(f"    {detail}")
        tests_failed += 1


print("\n" + "="*70)
print("PACK 4-6 SMOKE TESTS")
print("="*70)

# =============================================================================
# PACK 4: Weekly Module (System Audit)
# =============================================================================
print("\n📦 PACK 4: Weekly Module (P-WEEKLY-1)")
print("-" * 70)

from backend.app.core_gov.weekly import service as weekly_service

try:
    # Test 1: Run weekly check (no followups)
    result = weekly_service.run_weekly(create_followups=False)
    test("Run weekly check", result["ok"] is not None and "generated_at" in result,
         f"OK: {result['ok']}, Findings: {len(result['findings'])}")
    
    # Test 2: Check findings structure
    test("Weekly findings structure", isinstance(result.get("findings"), list),
         f"Found {len(result['findings'])} findings")
    
    # Test 3: Check response structure
    test("Weekly response structure", "created_followups" in result and "created_alerts" in result,
         f"Followups: {result['created_followups']}, Alerts: {result['created_alerts']}")
    
except Exception as e:
    test("PACK 4: Core functionality", False, f"Exception: {repr(e)}")

print(f"\n✅ PACK 4: Weekly Module: {tests_passed} tests passed")


# =============================================================================
# PACK 5: Automate Module (Rules/Triggers)
# =============================================================================
print("\n📦 PACK 5: Automate Module (P-AUTOMATE-1)")
print("-" * 70)

from backend.app.core_gov.automate import service as automate_service

try:
    # Test 1: Create rule
    rule_1 = automate_service.create_rule({
        "name": "Obligations not covered alert",
        "trigger": "obligations_not_covered",
        "action": "create_alert",
        "status": "active",
        "action_payload": {
            "title": "OBLIGATIONS NOT COVERED",
            "severity": "high",
            "message": "Obligations coverage issue detected.",
        },
    })
    test("Create rule: obligations_not_covered", rule_1["id"].startswith("rl_"),
         f"ID: {rule_1['id']}, trigger: {rule_1['trigger']}")
    
    # Test 2: Create another rule
    rule_2 = automate_service.create_rule({
        "name": "Shopping backlog alert",
        "trigger": "shopping_backlog_over",
        "threshold": 30,
        "action": "create_alert",
        "status": "active",
        "action_payload": {
            "title": "Shopping backlog over threshold",
            "severity": "low",
        },
    })
    test("Create rule: shopping_backlog_over", rule_2["id"].startswith("rl_"),
         f"ID: {rule_2['id']}, threshold: {rule_2['threshold']}")
    
    # Test 3: List rules
    rules = automate_service.list_rules()
    test("List rules", len(rules) >= 2, f"Found {len(rules)} rules")
    
    # Test 4: Filter by status
    active = automate_service.list_rules(status="active")
    test("Filter rules by status", len(active) >= 2,
         f"Found {len(active)} active rules")
    
    # Test 5: Filter by trigger
    oblig_rules = automate_service.list_rules(trigger="obligations_not_covered")
    test("Filter rules by trigger", len(oblig_rules) >= 1,
         f"Found {len(oblig_rules)} obligations rules")
    
    # Test 6: Evaluate rules (dry-run, no actions)
    eval_result = automate_service.evaluate(run_actions=False)
    test("Evaluate rules (dry-run)", eval_result["ok"] is True,
         f"Triggered: {eval_result['triggered']}, Results: {len(eval_result['results'])}")
    
    # Test 7: Check evaluation structure
    test("Evaluation response structure", "actions_executed" in eval_result,
         f"Actions executed: {eval_result['actions_executed']}")
    
except Exception as e:
    test("PACK 5: Core functionality", False, f"Exception: {repr(e)}")

print(f"\n✅ PACK 5: Automate Module: {tests_passed} tests passed")


# =============================================================================
# PACK 6: Credit Module (Business Credit)
# =============================================================================
print("\n📦 PACK 6: Credit Module (P-CREDIT-1)")
print("-" * 70)

from backend.app.core_gov.credit import service as credit_service

try:
    # Test 1: Upsert profile
    profile = credit_service.upsert_profile({
        "business_name": "Valhalla Test Inc.",
        "country": "CA",
        "province": "MB",
        "incorporation_date": "2026-01-02",
        "email": "test@valhalla.local",
    })
    test("Upsert credit profile", profile["business_name"] == "Valhalla Test Inc.",
         f"Business: {profile['business_name']}, Province: {profile['province']}")
    
    # Test 2: Create credit account
    account_1 = credit_service.create_account({
        "name": "Business Visa",
        "account_type": "credit_card",
        "credit_limit": 5000.0,
        "balance": 1200.0,
        "due_day": 15,
        "autopay": True,
    })
    test("Create credit account", account_1["id"].startswith("cr_"),
         f"ID: {account_1['id']}, utilization: {account_1['utilization']}%")
    account_1_id = account_1["id"]
    
    # Test 3: Verify utilization calculated
    test("Utilization calculated", account_1["utilization"] == 24.0,
         f"Balance: $1200, Limit: $5000, Util: {account_1['utilization']}%")
    
    # Test 4: Create vendor tradeline
    account_2 = credit_service.create_account({
        "name": "Uline Net-30",
        "account_type": "vendor_tradeline",
        "credit_limit": 2000.0,
        "balance": 500.0,
        "due_day": 30,
    })
    test("Create vendor tradeline", account_2["account_type"] == "vendor_tradeline",
         f"ID: {account_2['id']}, type: {account_2['account_type']}")
    account_2_id = account_2["id"]
    
    # Test 5: List accounts
    accounts = credit_service.list_accounts()
    test("List accounts", len(accounts) >= 2, f"Found {len(accounts)} accounts")
    
    # Test 6: Get totals
    totals = credit_service.totals()
    test("Calculate totals", totals["total_limit"] == 7000.0 and totals["total_balance"] == 1700.0,
         f"Limit: ${totals['total_limit']}, Balance: ${totals['total_balance']}, Util: {totals['total_utilization']}%")
    
    # Test 7: Update utilization
    updated = credit_service.update_utilization(account_1_id, balance=1800.0, credit_limit=5000.0)
    test("Update utilization", updated["balance"] == 1800.0 and updated["utilization"] == 36.0,
         f"New balance: ${updated['balance']}, New util: {updated['utilization']}%")
    
    # Test 8: Recommend next steps
    steps = credit_service.recommend_next_steps()
    test("Recommend next steps", len(steps) > 0 and isinstance(steps, list),
         f"Generated {len(steps)} recommendations")
    
    # Test 9: Add task
    task = credit_service.add_task(
        title="Pay down Visa",
        due_date="2026-01-15",
        priority="A",
    )
    test("Add credit task", task["id"].startswith("ct_"),
         f"ID: {task['id']}, title: {task['title']}, due: {task['due_date']}")
    
    # Test 10: List tasks
    tasks = credit_service.list_tasks(status="open")
    test("List credit tasks", len(tasks) >= 1,
         f"Found {len(tasks)} open tasks")
    
except Exception as e:
    test("PACK 6: Core functionality", False, f"Exception: {repr(e)}")

print(f"\n✅ PACK 6: Credit Module: {tests_passed} tests passed")


# =============================================================================
# Data Persistence Verification
# =============================================================================
print("\n📁 Data Persistence Verification")
print("-" * 70)

import os

persistence_checks = [
    ("backend/data/automate/rules.json", "Automate rules"),
    ("backend/data/credit/profile.json", "Credit profile"),
    ("backend/data/credit/accounts.json", "Credit accounts"),
    ("backend/data/credit/tasks.json", "Credit tasks"),
]

for path, desc in persistence_checks:
    exists = os.path.exists(path)
    if exists:
        try:
            with open(path, "r") as f:
                data = json.load(f)
                if "items" in data:
                    count = len(data.get("items", []))
                elif "profile" in data:
                    count = 1 if data["profile"] else 0
                else:
                    count = 0
                size = os.path.getsize(path)
                test(f"✓ {desc} persisted", True,
                     f"Path: {path} ({size} bytes, {count} items)")
        except Exception as e:
            test(f"✗ {desc} readable", False, f"Error: {repr(e)}")
    else:
        test(f"✗ {desc} exists", False, f"Path not found: {path}")


# =============================================================================
# Summary
# =============================================================================
print("\n" + "="*70)
print("FINAL RESULTS")
print("="*70)

total = tests_passed + tests_failed
pass_rate = (tests_passed / total * 100) if total > 0 else 0

print(f"\n✅ Tests Passed:  {tests_passed}")
print(f"❌ Tests Failed:  {tests_failed}")
print(f"📊 Total Tests:   {total}")
print(f"📈 Pass Rate:     {pass_rate:.1f}%")

if tests_failed == 0:
    print("\n" + "🎉 " * 10)
    print("ALL TESTS PASSED - PACK 4-6 DEPLOYMENT SUCCESSFUL!")
    print("🎉 " * 10)
    sys.exit(0)
else:
    print(f"\n⚠️  {tests_failed} test(s) failed. Review errors above.")
    sys.exit(1)
