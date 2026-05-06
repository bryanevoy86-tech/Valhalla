# Exact Commands to Run - Local Dev Testing

## Step 1: Stop Current Backend (if running)

### PowerShell
```powershell
# Kill uvicorn
Get-Process python | Where-Object {$_.CommandLine -match "uvicorn"} | Stop-Process -Force

# Wait for cleanup
Start-Sleep -Seconds 2
```

Or press `Ctrl+C` in the terminal where uvicorn is running.

---

## Step 2: Start Backend with Fixed Code

```bash
cd d:\dev
python -m uvicorn app.main:app --host 127.0.0.1 --port 4000 --reload
```

**Expected output (first 10 seconds):**
```
INFO:     Will watch for changes in these directories: ['D:\\dev']
INFO:     Uvicorn running on http://127.0.0.1:4000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using WatchFiles
INFO:     Valhalla startup complete. Loaded 230 router modules.
INFO:     CORS enabled for origins: [...]
```

**Verify:** You should see `Uvicorn running on http://127.0.0.1:4000` within 2-3 seconds.

---

## Step 3: Test Health Endpoint in Browser

```
http://127.0.0.1:4000/health
```

**Expected response:**
```json
{"ok":true,"status":"ok","heimdall":"online","routers_loaded":230}
```

**Should appear in browser in <100ms.**

---

## Step 4: Test Login Endpoint (PowerShell)

**Option A: With requests library (recommended)**

```powershell
python test_local_health.py
```

**Option B: Manual curl/PowerShell**

### Get Token
```powershell
$response = Invoke-WebRequest -Uri "http://127.0.0.1:4000/ops/token" `
  -Method POST `
  -Headers @{"Content-Type"="application/x-www-form-urlencoded"} `
  -Body "username=admin&password=admin-change-me" `
  -UseBasicParsing

$response.Content | ConvertFrom-Json | Format-List
```

**Expected response (200 OK):**
```
access_token : eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiIsImlhdCI6MTcxMzM5MDAwMCwiZXhwIjoxNzEzMzkzNjAwfQ...
token_type   : bearer
expires_in   : 3600
```

**Should respond in <500ms.**

---

## Step 5: Verify Token Works (PowerShell)

Save the token from Step 4, then:

```powershell
$token = "paste_the_access_token_from_step_4_here"

Invoke-WebRequest -Uri "http://127.0.0.1:4000/ops/me" `
  -Headers @{"Authorization"="Bearer $token"} `
  -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Expected response (200 OK):**
```json
{"ok":true,"user":"admin"}
```

---

## Credentials Reference

### For /ops/token (Use These)
| Field | Value |
|-------|-------|
| **username** | `admin` |
| **password** | `admin-change-me` |

### NOT /ops/token (For Future Use)
| Purpose | Email | Password |
|---------|-------|----------|
| Bootstrap Admin User (database) | `bryanevoy86@gmail.com` | `DrDoom!1` |

---

## Full Integration Test (One-Shot)

### PowerShell Script
```powershell
# 1. Check health
Write-Host "1. Testing health endpoint..."
$health = Invoke-WebRequest -Uri "http://127.0.0.1:4000/health" -UseBasicParsing | ConvertFrom-Json
Write-Host "✓ Health: $($health.status)"

# 2. Get token
Write-Host "2. Getting auth token..."
$auth = Invoke-WebRequest -Uri "http://127.0.0.1:4000/ops/token" `
  -Method POST `
  -Headers @{"Content-Type"="application/x-www-form-urlencoded"} `
  -Body "username=admin&password=admin-change-me" `
  -UseBasicParsing | ConvertFrom-Json
Write-Host "✓ Token type: $($auth.token_type)"

# 3. Verify token
Write-Host "3. Verifying token..."
$me = Invoke-WebRequest -Uri "http://127.0.0.1:4000/ops/me" `
  -Headers @{"Authorization"="Bearer $($auth.access_token)"} `
  -UseBasicParsing | ConvertFrom-Json
Write-Host "✓ Logged in as: $($me.user)"

Write-Host "`n✓ All tests passed! Ready for WeWeb integration."
```

Save as `test_backend.ps1` and run:
```powershell
.\test_backend.ps1
```

---

## Expected Timings

| Operation | Duration | Status |
|-----------|----------|--------|
| App startup to "Uvicorn running" | <3 seconds | ✓ Fast |
| GET /health | <100ms | ✓ Instant |
| POST /ops/token | <500ms | ✓ Quick |
| GET /ops/me (with token) | <100ms | ✓ Instant |
| Bootstrap admin completion | ~5 seconds after startup | ✓ Background |

---

## If Something Fails

### Backend won't start
```
Check: Is port 4000 already in use?
Fix:   netstat -ano | findstr :4000
Kill:  taskkill /PID <PID> /F
```

### Health endpoint returns 404
```
Check: Is backend running?
Fix:   Verify "Uvicorn running on http://127.0.0.1:4000" in logs
```

### /ops/token returns 401
```
Check: Are credentials correct?
Fix:   Use username=admin, password=admin-change-me
Fix:   Verify .env has VALHALLA_OWNER_USERNAME=admin
```

### /ops/token hangs/timeout
```
Check: Check startup logs for errors during auth settings load
Fix:   Ensure all required env vars are set (see .env)
```

---

## Next: WeWeb Integration

Once all tests pass:

1. **Open WeWeb editor**: https://editor.weweb.io
2. **Create REST API connector** with:
   - **Base URL:** `http://127.0.0.1:4000`
   - **Login endpoint:** `/ops/token`
   - **Methods:** Accept POST
3. **Test credentials**: admin / admin-change-me
4. **Build your UI pages** connected to Valhalla endpoints

---

## Quick Reference URLs

| Purpose | URL |
|---------|-----|
| Health check | http://127.0.0.1:4000/health |
| API docs | http://127.0.0.1:4000/docs |
| OpenAPI schema | http://127.0.0.1:4000/openapi.json |

---

**✓ Everything is ready. Start the backend and run the tests!**
