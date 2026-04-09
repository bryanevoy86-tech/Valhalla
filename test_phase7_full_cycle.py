#!/usr/bin/env python3
"""Phase 7 Full Cycle Test - Complete and close loop for remaining task"""
import requests
import json
import time

BASE_URL = "http://localhost:4000/api/jarvis"

print("\n" + "="*60)
print("PHASE 7 FULL CYCLE TEST - Close remaining task")
print("="*60)

# Step 1: Get tasks needing outcome
print("\n[1] Fetching tasks needing outcome...")
resp = requests.get(f"{BASE_URL}/tasks-needing-outcome")
data = resp.json()
tasks = data.get("items", [])
print(f"✓ Found {len(tasks)} tasks needing outcome")

if not tasks:
    print("✓ All tasks have outcomes recorded - loop closed!")
    exit(0)

task_to_close = tasks[0]
task_id = task_to_close.get("id")
contact_id = task_to_close.get("contact_id")

print(f"  Task ID: {task_id}, Contact: {contact_id}, Action: {task_to_close.get('action')}")

# Step 2: Record outcome for this task
print(f"\n[2] Recording outcome for Task {task_id}...")
outcome_payload = {
    "contact_id": contact_id,
    "result": "deal",
    "notes": "Contract signed and sent to legal.",
    "channel": "email",
    "task_id": task_id
}
resp = requests.post(f"{BASE_URL}/record-outcome", json=outcome_payload)
result = resp.json()
updated_task = result.get("task", {})
outcome = result.get("outcome", {})

print(f"✓ Outcome recorded")
print(f"  Outcome ID: {outcome.get('id')}")
print(f"  Outcome result: {outcome.get('result')}")
print(f"  Task outcome_recorded: {updated_task.get('outcome_recorded')}")

time.sleep(1)

# Step 3: Verify all tasks are now closed
print(f"\n[3] Verifying all tasks closed...")
resp = requests.get(f"{BASE_URL}/tasks-needing-outcome")
data = resp.json()
remaining_tasks = data.get("items", [])

print(f"✓ Tasks still needing outcome: {len(remaining_tasks)}")
if len(remaining_tasks) == 0:
    print("\n" + "="*60)
    print("✓✓✓ PHASE 7 FULL CYCLE SUCCESS ✓✓✓")
    print("    Task-to-Outcome Loop is Closed!")
    print("="*60 + "\n")
else:
    print(f"⚠ Still {len(remaining_tasks)} task(s) pending")
    for t in remaining_tasks:
        print(f"  - Task {t.get('id')}: {t.get('action')}")

# Step 4: Check audit logs
print("\n[4] Checking audit logs...")
try:
    with open("d:\\dev\\var\\jarvis_logs\\audit.jsonl", "r") as f:
        lines = f.readlines()
        recent = [json.loads(l) for l in lines[-5:]]
        print("✓ Recent audit events:")
        for event in recent:
            print(f"  - {event.get('event_type')}: {event.get('timestamp')}")
except Exception as e:
    print(f"⚠ Could not read audit logs: {e}")
