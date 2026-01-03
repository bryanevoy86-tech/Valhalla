#!/usr/bin/env python
"""
Comprehensive smoke tests for PACK 1-3 deployment:
- P-BUDGET-1: Household Buckets v1
- P-BUDGET-2: Transactions v1
- P-PACKS-1: Pack Registry
"""

import sys
import json
from datetime import datetime, date

# Test counters
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
print("PACK 1-3 SMOKE TESTS")
print("="*70)

# =============================================================================
# PACK 1: Budget Module (Household Buckets)
# =============================================================================
print("\n📦 PACK 1: Budget Module (P-BUDGET-1)")
print("-" * 70)

from backend.app.core_gov.budget import service as budget_service
from backend.app.core_gov.budget import store as budget_store

try:
    # Test 1: Create budget bucket
    bucket_1 = budget_service.create_bucket({
        "name": "Groceries",
        "bucket_type": "essentials",
        "monthly_limit": 900.0,
        "priority": "A",
        "rollover": False,
    })
    test("Create bucket: Groceries (essentials)", bucket_1["id"].startswith("bk_"), 
         f"ID: {bucket_1['id']}, limit: ${bucket_1['monthly_limit']}")
    bk_id_1 = bucket_1["id"]
    
    # Test 2: Create another bucket
    bucket_2 = budget_service.create_bucket({
        "name": "Entertainment",
        "bucket_type": "fun",
        "monthly_limit": 200.0,
        "priority": "C",
    })
    test("Create bucket: Entertainment (fun)", bucket_2["id"].startswith("bk_"),
         f"ID: {bucket_2['id']}, limit: ${bucket_2['monthly_limit']}")
    bk_id_2 = bucket_2["id"]
    
    # Test 3: List buckets
    buckets = budget_service.list_buckets()
    test("List buckets", len(buckets) >= 2, f"Found {len(buckets)} buckets")
    
    # Test 4: Get bucket
    retrieved = budget_service.get_bucket(bk_id_1)
    test("Get bucket by ID", retrieved is not None and retrieved["name"] == "Groceries",
         f"Name: {retrieved.get('name') if retrieved else 'N/A'}")
    
    # Test 5: Patch bucket
    patched = budget_service.patch_bucket(bk_id_1, {"notes": "Updated for Jan 2026"})
    test("Patch bucket", patched["notes"] == "Updated for Jan 2026",
         f"Notes: {patched['notes']}")
    
    # Test 6: Get monthly snapshot (auto-creates)
    snaps = budget_service.get_month("2026-01")
    test("Get month snapshot (2026-01)", len(snaps) >= 2,
         f"Got {len(snaps)} snapshots for month")
    
    # Test 7: Verify bucket limits in snapshot
    snap_1 = next((s for s in snaps if s["bucket_id"] == bk_id_1), None)
    test("Month snapshot includes Groceries", snap_1 is not None,
         f"Remaining: ${snap_1['remaining'] if snap_1 else 'N/A'}")
    
    # Test 8: Set allocation
    alloc = budget_service.set_allocation("2026-01", bk_id_2, 150.0)
    test("Set manual allocation", alloc["allocated"] == 150.0,
         f"Allocated: ${alloc['allocated']}")
    
except Exception as e:
    test("PACK 1: Core functionality", False, f"Exception: {repr(e)}")

print(f"\n✅ PACK 1: Budget Module Summary: {tests_passed} tests passed")


# =============================================================================
# PACK 2: Transactions Module
# =============================================================================
print("\n📦 PACK 2: Transactions Module (P-BUDGET-2)")
print("-" * 70)

from backend.app.core_gov.transactions import service as tx_service
from backend.app.core_gov.transactions import store as tx_store

try:
    # Test 1: Create expense transaction (should touch budget)
    tx_1 = tx_service.create_tx({
        "tx_type": "expense",
        "amount": 120.0,
        "date": "2026-01-02",
        "description": "Walmart groceries",
        "bucket_id": bk_id_1,
        "priority": "B",
        "category": "groceries",
    })
    test("Create expense (bucket tracked)", tx_1["id"].startswith("tx_"),
         f"ID: {tx_1['id']}, amount: ${tx_1['amount']}")
    tx_id_1 = tx_1["id"]
    
    # Test 2: Verify budget was updated
    snaps_after = budget_service.get_month("2026-01")
    snap_updated = next((s for s in snaps_after if s["bucket_id"] == bk_id_1), None)
    budget_spent = snap_updated["spent"] if snap_updated else 0
    test("Budget spent updated", budget_spent == 120.0,
         f"Spent: ${budget_spent}, Remaining: ${snap_updated['remaining'] if snap_updated else 'N/A'}")
    
    # Test 3: Create income transaction
    tx_2 = tx_service.create_tx({
        "tx_type": "income",
        "amount": 3000.0,
        "date": "2026-01-01",
        "description": "Monthly salary",
        "priority": "A",
    })
    test("Create income transaction", tx_2["id"].startswith("tx_"),
         f"ID: {tx_2['id']}, amount: ${tx_2['amount']}")
    
    # Test 4: List transactions
    all_txs = tx_service.list_txs()
    test("List all transactions", len(all_txs) >= 2,
         f"Found {len(all_txs)} transactions")
    
    # Test 5: Filter by type
    expenses = tx_service.list_txs(tx_type="expense")
    test("Filter by tx_type=expense", len(expenses) >= 1,
         f"Found {len(expenses)} expenses")
    
    # Test 6: Filter by bucket
    bucket_txs = tx_service.list_txs(bucket_id=bk_id_1)
    test("Filter by bucket_id", len(bucket_txs) >= 1,
         f"Found {len(bucket_txs)} transactions for bucket")
    
    # Test 7: Filter by month
    month_txs = tx_service.list_txs(month="2026-01")
    test("Filter by month", len(month_txs) >= 2,
         f"Found {len(month_txs)} transactions for 2026-01")
    
    # Test 8: Void transaction
    voided = tx_service.void_tx(tx_id_1)
    test("Void transaction", voided["status"] == "void",
         f"Status: {voided['status']}")
    
    # Test 9: Verify budget was reversed
    snaps_voided = budget_service.get_month("2026-01")
    snap_voided = next((s for s in snaps_voided if s["bucket_id"] == bk_id_1), None)
    budget_after_void = snap_voided["spent"] if snap_voided else 0
    test("Budget reversed on void", budget_after_void == 0.0,
         f"Spent after void: ${budget_after_void}")
    
except Exception as e:
    test("PACK 2: Core functionality", False, f"Exception: {repr(e)}")

print(f"\n✅ PACK 2: Transactions Module Summary: {tests_passed} tests passed")


# =============================================================================
# PACK 3: Packs Registry Module
# =============================================================================
print("\n📦 PACK 3: Packs Registry (P-PACKS-1)")
print("-" * 70)

from backend.app.core_gov.packs import service as packs_service
from backend.app.core_gov.packs import store as packs_store

try:
    # Test 1: Register P-BUDGET-1 pack
    pack_1 = packs_service.create_pack({
        "code": "P-BUDGET-1",
        "name": "Household Buckets v1",
        "module": "backend.app.core_gov.budget",
        "router_symbol": "budget_router",
        "data_paths": [
            "backend/data/budget/buckets.json",
            "backend/data/budget/snapshots.json",
        ],
        "tags": ["budget", "essentials"],
    })
    test("Register P-BUDGET-1 pack", pack_1["id"].startswith("pk_"),
         f"ID: {pack_1['id']}, code: {pack_1['code']}")
    
    # Test 2: Register P-BUDGET-2 pack
    pack_2 = packs_service.create_pack({
        "code": "P-BUDGET-2",
        "name": "Transactions v1",
        "module": "backend.app.core_gov.transactions",
        "router_symbol": "transactions_router",
        "data_paths": ["backend/data/transactions/transactions.json"],
        "tags": ["transactions", "money"],
    })
    test("Register P-BUDGET-2 pack", pack_2["id"].startswith("pk_"),
         f"ID: {pack_2['id']}, code: {pack_2['code']}")
    
    # Test 3: Register P-PACKS-1 pack (self-reference)
    pack_3 = packs_service.create_pack({
        "code": "P-PACKS-1",
        "name": "Pack Registry",
        "module": "backend.app.core_gov.packs",
        "router_symbol": "packs_router",
        "data_paths": ["backend/data/packs/packs.json"],
        "tags": ["registry", "system"],
    })
    test("Register P-PACKS-1 pack (self)", pack_3["id"].startswith("pk_"),
         f"ID: {pack_3['id']}, code: {pack_3['code']}")
    
    # Test 4: List all packs
    all_packs = packs_service.list_packs()
    test("List all packs", len(all_packs) >= 3,
         f"Found {len(all_packs)} packs registered")
    
    # Test 5: Filter by tag
    budget_packs = packs_service.list_packs(tag="budget")
    test("Filter packs by tag", len(budget_packs) >= 1,
         f"Found {len(budget_packs)} packs with tag 'budget'")
    
    # Test 6: Validate packs (imports + routers)
    validation = packs_service.validate()
    test("Validate pack imports", validation["ok"],
         f"Checked: {validation['checked']}, Errors: {len(validation['errors'])}, Warnings: {len(validation['warnings'])}")
    
    if validation["errors"]:
        for err in validation["errors"]:
            print(f"    ERROR: {err}")
    
    if validation["warnings"]:
        for warn in validation["warnings"]:
            print(f"    WARNING: {warn}")
    
except Exception as e:
    test("PACK 3: Core functionality", False, f"Exception: {repr(e)}")

print(f"\n✅ PACK 3: Packs Registry Summary: {tests_passed} tests passed")


# =============================================================================
# Data Persistence Verification
# =============================================================================
print("\n📁 Data Persistence Verification")
print("-" * 70)

import os

persistence_checks = [
    ("backend/data/budget/buckets.json", "Budget buckets"),
    ("backend/data/budget/snapshots.json", "Budget snapshots"),
    ("backend/data/transactions/transactions.json", "Transactions ledger"),
    ("backend/data/packs/packs.json", "Packs registry"),
]

for path, desc in persistence_checks:
    exists = os.path.exists(path)
    if exists:
        try:
            with open(path, "r") as f:
                data = json.load(f)
                count = len(data.get("items", []))
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
    print("ALL TESTS PASSED - PACK 1-3 DEPLOYMENT SUCCESSFUL!")
    print("🎉 " * 10)
    sys.exit(0)
else:
    print(f"\n⚠️  {tests_failed} test(s) failed. Review errors above.")
    sys.exit(1)
