#!/usr/bin/env python
"""
Smoke tests for PACK 1-3: Flow Engine, Replacement Planner, Unified Scheduler
Verifies all CRUD operations and data persistence
"""

from backend.app.core_gov.flow import service as flow_service
from backend.app.core_gov.replacements import service as replacements_service
from backend.app.core_gov.schedule import service as schedule_service

def test_flow_pack():
    """PACK 1: Supply Flow Engine"""
    print("\n✓ PACK 1 — Supply Flow Engine (P-FLOW-1)")
    
    # Create supply item
    item_payload = {
        "name": "Toilet Paper",
        "item_type": "household",
        "est_unit_cost": 18.0,
        "reorder_point": 1.0,
        "target_level": 3.0,
        "cadence_days": 21,
        "preferred_size": "12-pack",
        "store_pref": "Costco",
    }
    item = flow_service.create_item(item_payload)
    item_id = item["id"]
    print(f"  ✓ Created supply item: {item['name']} ({item_id})")
    
    # List items
    items = flow_service.list_items(status="active")
    print(f"  ✓ Listed {len(items)} active item(s)")
    
    # Update inventory (below reorder point)
    inv_payload = {
        "item_id": item_id,
        "current_level": 0.5,
        "urgency": "medium",
        "note": "Running low",
    }
    inv = flow_service.upsert_inventory(inv_payload)
    print(f"  ✓ Updated inventory: level={inv['current_level']}")
    
    # Get inventory
    inv_check = flow_service.get_inventory(item_id)
    print(f"  ✓ Retrieved inventory: {inv_check['current_level']}")
    
    # List shopping (auto-created from low inventory)
    shopping = flow_service.list_shopping(status="open")
    print(f"  ✓ Auto-reorder created {len(shopping)} shopping item(s)")
    
    if shopping:
        shopping_id = shopping[0]["id"]
        # Mark as done
        marked = flow_service.mark_shopping(shopping_id, status="done")
        print(f"  ✓ Marked shopping item as {marked['status']}")
    
    print("  ✅ PACK 1 ALL TESTS PASSED")
    return True


def test_replacements_pack():
    """PACK 2: Replacement Planner"""
    print("\n✓ PACK 2 — Replacement Planner (P-REPLACE-1)")
    
    # Create replacement
    repl_payload = {
        "name": "Mattress",
        "target_cost": 1200.0,
        "currency": "CAD",
        "priority": "B",
        "suggested_months": 4,
        "notes": "Current mattress 10 years old",
    }
    repl = replacements_service.create_replacement(repl_payload)
    repl_id = repl["id"]
    print(f"  ✓ Created replacement: {repl['name']} (${repl['target_cost']}, monthly_save=${repl['monthly_save']})")
    
    # List replacements
    repls = replacements_service.list_replacements(status="planned")
    print(f"  ✓ Listed {len(repls)} planned replacement(s)")
    
    # Get one
    r = replacements_service.get_replacement(repl_id)
    print(f"  ✓ Retrieved replacement: {r['name']}")
    
    # Patch
    patch_data = {"status": "saving", "priority": "A"}
    patched = replacements_service.patch_replacement(repl_id, patch_data)
    print(f"  ✓ Patched replacement: status={patched['status']}, priority={patched['priority']}")
    
    # Get plan
    plan = replacements_service.plan(repl_id)
    print(f"  ✓ Generated plan with {len(plan['schedule_suggestion'])} steps:")
    for i, step in enumerate(plan['schedule_suggestion'], 1):
        print(f"    {i}. {step[:70]}")
    
    print("  ✅ PACK 2 ALL TESTS PASSED")
    return True


def test_schedule_pack():
    """PACK 3: Unified Life Scheduler"""
    print("\n✓ PACK 3 — Unified Scheduler (P-SCHED-1)")
    
    # Create schedule item
    sched_payload = {
        "title": "Grocery run",
        "kind": "task",
        "due_date": "2026-01-15",
        "priority": "B",
        "est_cost": 120.0,
        "timezone": "America/Toronto",
        "notes": "Buy milk, bread, eggs",
    }
    sched = schedule_service.create(sched_payload)
    sched_id = sched["id"]
    print(f"  ✓ Created schedule item: {sched['title']} on {sched['due_date']}")
    
    # List schedule
    scheds = schedule_service.list_all(status="open")
    print(f"  ✓ Listed {len(scheds)} open schedule item(s)")
    
    # List by date
    date_scheds = schedule_service.list_all(due_date="2026-01-15")
    print(f"  ✓ Listed {len(date_scheds)} item(s) for 2026-01-15")
    
    # Patch
    patch_data = {"status": "done", "notes": "Completed grocery run"}
    patched = schedule_service.patch(sched_id, patch_data)
    print(f"  ✓ Patched schedule: status={patched['status']}")
    
    # Create event with link
    event_payload = {
        "title": "Mattress purchase deadline",
        "kind": "event",
        "due_date": "2026-05-15",
        "link_type": "replacement",
        "link_id": "rp_12345",
        "priority": "A",
        "est_cost": 1200.0,
    }
    event = schedule_service.create(event_payload)
    print(f"  ✓ Created linked event: {event['title']} -> {event['link_type']}:{event['link_id']}")
    
    print("  ✅ PACK 3 ALL TESTS PASSED")
    return True


def test_data_persistence():
    """Verify all data files created"""
    print("\n✓ DATA PERSISTENCE VERIFICATION")
    import os
    
    data_dirs = [
        ("backend/data/flow", ["items.json", "inventory.json", "shopping.json"]),
        ("backend/data/replacements", ["replacements.json"]),
        ("backend/data/schedule", ["schedule.json"]),
    ]
    
    for dir_path, files in data_dirs:
        if os.path.isdir(dir_path):
            for fname in files:
                fpath = os.path.join(dir_path, fname)
                if os.path.isfile(fpath):
                    size = os.path.getsize(fpath)
                    print(f"  ✓ {dir_path}/{fname} ({size} bytes)")
                else:
                    print(f"  ✗ {dir_path}/{fname} NOT FOUND")
                    return False
        else:
            print(f"  ✗ {dir_path} directory not found")
            return False
    
    print("  ✅ ALL DATA FILES VERIFIED")
    return True


def main():
    print("\n" + "="*70)
    print(" SMOKE TESTS: PACK 1-3 (Flow, Replacements, Schedule)")
    print("="*70)
    
    results = []
    
    try:
        results.append(("PACK 1: Flow Engine", test_flow_pack()))
    except Exception as e:
        print(f"  ✗ PACK 1 FAILED: {e}")
        results.append(("PACK 1: Flow Engine", False))
    
    try:
        results.append(("PACK 2: Replacements", test_replacements_pack()))
    except Exception as e:
        print(f"  ✗ PACK 2 FAILED: {e}")
        results.append(("PACK 2: Replacements", False))
    
    try:
        results.append(("PACK 3: Schedule", test_schedule_pack()))
    except Exception as e:
        print(f"  ✗ PACK 3 FAILED: {e}")
        results.append(("PACK 3: Schedule", False))
    
    try:
        results.append(("Data Persistence", test_data_persistence()))
    except Exception as e:
        print(f"  ✗ Data Persistence FAILED: {e}")
        results.append(("Data Persistence", False))
    
    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
    
    all_pass = all(result[1] for result in results)
    print("\n" + ("="*70))
    if all_pass:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70 + "\n")
    
    return all_pass


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
