# Builder API /apply Endpoint - Curl Examples

## Environment Setup
export API="http://localhost:8000/api"
export HEIMDALL_BUILDER_API_KEY="your-long-random-secret"

## Step 1: Create a task (stores draft in payload_json)
curl -X POST "$API/builder/tasks" \
  -H "X-API-Key: $HEIMDALL_BUILDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add /reports router",
    "scope": "services/api/app/routers/reports.py",
    "plan": "create router with /reports/summary"
  }'

# Response includes task_id and files array

## Step 2: Review draft (approve=false) - SAFE, doesn't write files
curl -X POST "$API/builder/apply" \
  -H "X-API-Key: $HEIMDALL_BUILDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"task_id":1,"approve":false}'

# Returns: {"task_id":1, "files":[...], "diff_summary":"..."}

## Step 3: Apply changes (approve=true) - WRITES FILES TO DISK
curl -X POST "$API/builder/apply" \
  -H "X-API-Key: $HEIMDALL_BUILDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"task_id":1,"approve":true}'

# Guardrails enforced:
# - Path must be in BUILDER_ALLOWED_DIRS (configured in settings.py)
# - File size must be under BUILDER_MAX_FILE_BYTES (default: 200KB)
# - Mode must be "add" or "replace"
# 
# On success:
# - Files are written to disk
# - Task status set to "applied"
# - BuilderEvent logged with "apply" kind
# - Returns: {"task_id":1, "files":[...], "diff_summary":"applied N files"}

## PowerShell equivalent (Windows)
# $env:API="http://localhost:8000/api"
# $env:HEIMDALL_BUILDER_API_KEY="your-long-random-secret"
# 
# # Review (safe)
# curl.exe -X POST "$env:API/builder/apply" `
#   -H "X-API-Key: $env:HEIMDALL_BUILDER_API_KEY" `
#   -H "Content-Type: application/json" `
#   -d "{\"task_id\":1,\"approve\":false}"
#
# # Apply (writes files)
# curl.exe -X POST "$env:API/builder/apply" `
#   -H "X-API-Key: $env:HEIMDALL_BUILDER_API_KEY" `
#   -H "Content-Type: application/json" `
#   -d "{\"task_id\":1,\"approve\":true}"
