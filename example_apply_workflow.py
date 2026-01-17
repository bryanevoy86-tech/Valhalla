#!/usr/bin/env python3
"""
Builder API Apply Endpoint Example

This demonstrates the /apply endpoint workflow:
1. Create a task with /tasks endpoint (stores files in payload_json)
2. Review the draft with /apply (approve=false)
3. Apply changes with /apply (approve=true) - writes files to disk

The /apply endpoint:
- With approve=false: Returns the draft for review (doesn't write files)
- With approve=true: Writes files to disk with guardrails:
  - Path whitelisting (BUILDER_ALLOWED_DIRS)
  - File size limits (BUILDER_MAX_FILE_BYTES)
  - Mode validation (add, replace)
"""

import os
import json
import requests

# Configuration
API = os.environ.get("API", "http://localhost:8000/api")
KEY = os.environ.get("KEY", "your-long-random-secret")

print("=== Builder API /apply Workflow ===\n")

# Step 1: Create a task (this stores the draft in payload_json)
print("Step 1: Creating task with file changes...")
task_response = requests.post(
    f"{API}/builder/tasks",
    headers={"X-API-Key": KEY, "Content-Type": "application/json"},
    json={
        "title": "Add /reports router",
        "scope": "services/api/app/routers/reports.py",
        "plan": "create router with /reports/summary endpoint"
    }
)
task_response.raise_for_status()
task_data = task_response.json()
task_id = task_data["id"]
print(f"✓ Task created: ID={task_id}")
print(f"  Draft files: {len(task_data.get('files', []))} file(s)\n")

# Step 2: Review the draft (approve=false)
print(f"Step 2: Reviewing draft for task {task_id}...")
review_response = requests.post(
    f"{API}/builder/apply",
    headers={"X-API-Key": KEY, "Content-Type": "application/json"},
    json={"task_id": task_id, "approve": False}
)
review_response.raise_for_status()
draft = review_response.json()
print(f"✓ Draft retrieved:")
print(f"  Task ID: {draft['task_id']}")
print(f"  Files: {len(draft.get('files', []))}")
print(f"  Summary: {draft.get('diff_summary', 'N/A')}")
for file_spec in draft.get('files', []):
    print(f"    - {file_spec['path']} ({file_spec.get('mode', 'add')})")
print()

# Step 3: Apply changes (approve=true) - this writes files!
print(f"Step 3: Applying changes for task {task_id}...")
print("⚠️  This will write files to disk with guardrails:")
print("   - Path must be in BUILDER_ALLOWED_DIRS")
print("   - File size must be under BUILDER_MAX_FILE_BYTES")
print("   - Mode must be 'add' or 'replace'\n")

# Uncomment to actually apply:
# apply_response = requests.post(
#     f"{API}/builder/apply",
#     headers={"X-API-Key": KEY, "Content-Type": "application/json"},
#     json={"task_id": task_id, "approve": True}
# )
# apply_response.raise_for_status()
# result = apply_response.json()
# print(f"✓ Changes applied:")
# print(f"  Summary: {result.get('diff_summary')}")
# print(f"  Files written: {len(result.get('files', []))}")

print("(Skipped actual file writing - uncomment to enable)")
print("\n=== Workflow Complete ===")
