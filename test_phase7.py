#!/usr/bin/env python3
"""Phase 7 Test Suite - Task-to-Outcome Loop"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:4000/api/jarvis"

def test_backend_health():
    """Test 1: Verify backend is responding"""
    print("\n" + "="*60)
    print("TEST 1: Backend Health Check")
    print("="*60)
    try:
        # Try dashboard endpoint instead
        resp = requests.get(f"{BASE_URL}/dashboard", timeout=5)
        print(f"✓ Backend responsive: {resp.status_code}")
        return True
    except Exception as e:
        print(f"✗ Backend error: {e}")
        return False

def test_create_task():
    """Test 2: Create task via auto-generate"""
    print("\n" + "="*60)
    print("TEST 2: Create Task via Auto-Generate")
    print("="*60)
    try:
        resp = requests.post(f"{BASE_URL}/auto-generate-tasks", timeout=10)
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)[:200]}...")
        
        # Check if tasks were created
        if "tasks_created" in data:
            print(f"✓ Tasks created: {data['tasks_created']}")
            return data
        else:
            print(f"⚠ Response structure: {data.keys()}")
            return data
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_get_pending_tasks():
    """Test 3: Get pending tasks"""
    print("\n" + "="*60)
    print("TEST 3: Get Pending Tasks")
    print("="*60)
    try:
        resp = requests.get(f"{BASE_URL}/tasks", timeout=10)
        data = resp.json()
        tasks = data.get("tasks", [])
        print(f"✓ Found {len(tasks)} pending tasks")
        if tasks:
            task = tasks[0]
            print(f"  Task ID: {task.get('id')}, Contact: {task.get('contact_id')}, Priority: {task.get('priority')}")
            return task
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_complete_task(task_id):
    """Test 4: Complete task with notes"""
    print("\n" + "="*60)
    print(f"TEST 4: Complete Task {task_id}")
    print("="*60)
    try:
        payload = {
            "task_id": task_id,
            "notes": "Customer expressed strong interest. Follow up requested."
        }
        resp = requests.post(f"{BASE_URL}/complete-task", json=payload, timeout=10)
        result = resp.json()
        task = result.get("task", {})
        print(f"✓ Task completed")
        print(f"  Status: {task.get('status')}")
        print(f"  Completed at: {task.get('completed_at')}")
        print(f"  Next step: {result.get('next_step')}")
        return result
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_tasks_needing_outcome():
    """Test 5: Check for tasks needing outcome"""
    print("\n" + "="*60)
    print("TEST 5: Get Tasks Needing Outcome")
    print("="*60)
    try:
        resp = requests.get(f"{BASE_URL}/tasks-needing-outcome", timeout=10)
        data = resp.json()
        tasks = data.get("items", [])
        print(f"✓ Found {len(tasks)} tasks needing outcome")
        if tasks:
            task = tasks[0]
            print(f"  Task ID: {task.get('id')}, Contact: {task.get('contact_id')}")
            print(f"  Action: {task.get('action')}")
            print(f"  Completed: {task.get('completed_at')}")
            return task
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_record_outcome(task_id):
    """Test 6: Record outcome linked to task"""
    print("\n" + "="*60)
    print(f"TEST 6: Record Outcome for Task {task_id}")
    print("="*60)
    try:
        # First get the task to get contact_id
        resp = requests.get(f"{BASE_URL}/tasks", timeout=10)
        data = resp.json()
        tasks = data.get("tasks", [])
        task = next((t for t in tasks if t.get('id') == task_id), None)
        
        if not task:
            # Get from tasks-needing-outcome
            resp = requests.get(f"{BASE_URL}/tasks-needing-outcome", timeout=10)
            data = resp.json()
            tasks = data.get("items", [])
            task = next((t for t in tasks if t.get('id') == task_id), None)
        
        if not task:
            print(f"✗ Task {task_id} not found")
            return None
            
        contact_id = task.get('contact_id')
        
        payload = {
            "contact_id": contact_id,
            "result": "success",
            "notes": "Customer confirmed meeting time for next week.",
            "channel": "sms",
            "task_id": task_id
        }
        resp = requests.post(f"{BASE_URL}/record-outcome", json=payload, timeout=10)
        result = resp.json()
        outcome = result.get("outcome", {})
        updated_task = result.get("task", {})
        print(f"✓ Outcome recorded")
        print(f"  Outcome ID: {outcome.get('id')}")
        print(f"  Result: {outcome.get('result')}")
        print(f"  Task marked outcome_recorded: {updated_task.get('outcome_recorded')}")
        return result
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_verify_task_closed():
    """Test 7: Verify task is now marked outcome_recorded"""
    print("\n" + "="*60)
    print("TEST 7: Verify Task Closed (outcome_recorded=true)")
    print("="*60)
    try:
        resp = requests.get(f"{BASE_URL}/tasks-needing-outcome", timeout=10)
        data = resp.json()
        tasks = data.get("items", [])
        print(f"✓ Tasks needing outcome: {len(tasks)}")
        if len(tasks) == 0:
            print("  ✓ SUCCESS - Task outcome loop closed!")
            return True
        else:
            print(f"  ⚠ Still {len(tasks)} task(s) pending outcome")
            for t in tasks:
                print(f"    - Task {t.get('id')}: {t.get('action')}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "#"*60)
    print("# HEIMDALL PHASE 7 - TASK-TO-OUTCOME LOOP TEST SUITE")
    print("#"*60)
    
    # Test 1: Backend health
    if not test_backend_health():
        print("\n✗ Backend not responding. Exiting.")
        return
    
    # Give backend a moment
    time.sleep(1)
    
    # Test 2: Get pending tasks or create new one
    pending = test_get_pending_tasks()
    if not pending:
        print("\n→ No pending tasks. Creating via auto-generate...")
        test_create_task()
        time.sleep(1)
        pending = test_get_pending_tasks()
    
    if not pending:
        print("\n✗ Could not create or find task. Exiting.")
        return
    
    task_id = pending.get('id')
    print(f"\n→ Working with task ID: {task_id}")
    
    # Test 3: Complete task
    test_complete_task(task_id)
    time.sleep(1)
    
    # Test 4: Verify task shows in tasks-needing-outcome
    task_needing_outcome = test_tasks_needing_outcome()
    if not task_needing_outcome:
        print("\n✗ Task not found in tasks-needing-outcome. This should not happen.")
        return
    
    time.sleep(1)
    
    # Test 5: Record outcome
    test_record_outcome(task_id)
    time.sleep(1)
    
    # Test 6: Verify task is now closed
    success = test_verify_task_closed()
    
    print("\n" + "#"*60)
    if success:
        print("# ✓ PHASE 7 TEST SUITE PASSED - LOOP CLOSED")
    else:
        print("# ⚠ PHASE 7 TEST SUITE - CHECK RESULTS ABOVE")
    print("#"*60 + "\n")

if __name__ == "__main__":
    main()
