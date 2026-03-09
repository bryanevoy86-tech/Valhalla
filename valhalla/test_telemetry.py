import os, json, requests

API = os.environ.get("API", "http://localhost:8000/api")
KEY = os.environ.get("KEY", "your-long-random-secret")
TASK_ID = int(os.environ.get("TASK_ID", "1"))

files = [{
    "path": "services/api/app/routers/reports.py",
    "mode": "add",
    "content": "from fastapi import APIRouter\nrouter=APIRouter(prefix='/reports')\n@router.get('/summary')\ndef summary():\n    return {'ok': True}\n"
}]

payload = {"task_id": TASK_ID, "approve": False}

# First, stash draft into task row (reuse /telemetry to set payload_json via /apply pattern)
# In practice, you'd have a helper endpoint to update the draft. For now, we simulate by calling /telemetry with meta_json=files.
response = requests.post(
    f"{API}/builder/telemetry",
    headers={"X-API-Key": KEY, "Content-Type": "application/json"},
    json={"kind": "draft", "msg": f"task:{TASK_ID}", "meta_json": json.dumps(files)}
)
response.raise_for_status()
print("Draft uploaded via telemetry (stored in events log). Manually set payload_json in DB if needed.")
print(f"Response: {response.json()}")
