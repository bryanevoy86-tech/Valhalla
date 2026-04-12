# WEWEB RECONNECT CHECKLIST

**Use this checklist when WeWeb tokens come back online**

---

## PRE-RECONNECT (Before restarting WeWeb)

### ✓ Confirm Backend is Running

```bash
# From any terminal at d:\dev
curl http://localhost:4000/health -s | jq .
```

**Expected:**
```json
{
  "ok": true,
  "status": "ok",
  "heimdall": "online",
  "routers_loaded": 220+
}
```

**If not responding:** Start server with:
```bash
$env:DATABASE_URL='sqlite:///./valhalla_local.db'
$env:VALHALLA_JWT_SECRET='dev-secret-key'
$env:BUILDER_KEY='your-secure-key'
$env:CORS_ALLOWED_ORIGINS='["http://localhost:3000"]'
python -m uvicorn app.main:app --reload --port 4000
```

---

## RECONNECT SEQUENCE (Do in this exact order)

### STEP 1: Verify Execution Layer Is Ready

**Test:** Create test intake

```bash
curl -X POST http://localhost:4000/execution/intake \
  -H "Content-Type: application/json" \
  -d '{"raw_text":"Test property for verification"}'
```

**Expected:** Returns `intake_id` and status `"new"`

**If fails:** ❌ Stop here. Execution layer not ready.

**If passes:** ✅ Continue to STEP 2

---

### STEP 2: Verify Pipeline Execution

**Test:** Process the intake

```bash
curl -X POST http://localhost:4000/execution/intake/1/process \
  -H "Content-Type: application/json" \
  -d '{"intake_id":1}'
```

**Expected:** Returns case summary with:
- `case_id` (integer)
- `classification` (string)
- `estimated_profit` (number)
- `recommended_strategy` (string)
- `tasks_created` (integer)

**If fails:** ❌ Check execution service logs. Database issue?

**If passes:** ✅ Continue to STEP 3

---

### STEP 3: Verify Task Generation

**Test:** Get task list

```bash
curl http://localhost:4000/execution/cases/1/tasks
```

**Expected:** Returns task list with 3+ tasks, each with:
- `id`
- `title` (action verb)
- `instructions`
- `priority`
- `sequence`

**If empty:** ❌ Task generation failed. Check services.

**If passes:** ✅ Continue to STEP 4

---

### STEP 4: Configure CORS (If Using Browser)

**Check if CORS middleware is active:**

```bash
curl -X OPTIONS http://localhost:4000/execution/intake \
  -H "Origin: http://localhost:3000" \
  -v
```

**Look for response headers:**
- `Access-Control-Allow-Origin: http://localhost:3000`
- `Access-Control-Allow-Methods: GET, POST, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type`

**If CORS headers missing:** 
- CORS middleware needs to be activated in main.py
- (This is a PHASE 6 fix if needed)

**If CORS headers present:** ✅ Continue to STEP 5

---

### STEP 5: Build First Page in WeWeb

**You are now ready to:**
1. Create new WeWeb data source connected to `http://localhost:4000/execution/intake`
2. Build intake form:
   - Input field: `raw_text` (textarea, required)
   - Button: "Create Intake"
   - Display: `intake_id` returned
3. Create second data source: `http://localhost:4000/execution/intake/{intake_id}/process`
4. Build processing display:
   - Show: case summary (value, profit, strategy)
   - Show: task list (title + instructions)
   - Show: next action

**After first page works:** ✅ Continue to STEP 6

---

### STEP 6: Test Builder Integration (Optional - If Using Heimdall)

**Test:** Register builder

```bash
curl -X POST http://localhost:4000/builder/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-builder-key" \
  -d '{"agent_name":"heimdall-v1","version":"1.0"}'
```

**Expected:** `{"ok": true, "message": "Welcome..."}`

**If fails:** ❌ Builder key not set in environment or incorrect.

**If passes:** ✅ Builder ready for co-build phase

---

## STOP RULES (Don't waste tokens)

### 🛑 STOP if any of these happen:

1. **Intake creation fails (not 200)**
   - Backend or database issue
   - Check server logs

2. **Process returns incomplete response**
   - Fields missing
   - Task count = 0 when expected >0
   - Check services

3. **CORS blocks browser requests**
   - Frontend can't reach backend
   - Need to add CORS middleware before WeWeb reconnect

4. **Any 500 error in response**
   - Server error
   - Check logs, don't proceed

5. **Task list is empty**
   - Task generation broken
   - Fix before WeWeb connects

### 🟢 SAFE to proceed to WeWeb if all return:
- ✅ Intake: 200 + intake_id
- ✅ Process: 200 + full case summary
- ✅ Tasks: 200 + 3+ tasks with sequence
- ✅ CORS: Allow-Origin header present (if browser)

---

## QUICK SUMMARY

**What to do:**
1. Verify health endpoint responds
2. Test intake creation
3. Test pipeline processing
4. Test task generation
5. Verify CORS if needed
6. Start building in WeWeb

**How long:** ~2 minutes to verify all steps

**What happens if blocked:** Fix the specific step that failed, then restart from STEP 1

---

## ENVIRONMENT SETUP (Reference)

**Before starting backend:**

```bash
cd d:\dev

# Set environment variables
$env:DATABASE_URL='sqlite:///./valhalla_local.db'
$env:VALHALLA_JWT_SECRET='dev-secret-key'
$env:BUILDER_KEY='your-security-key-here'
$env:CORS_ALLOWED_ORIGINS='["http://localhost:3000","http://localhost:5173"]'

# Start server
python -m uvicorn app.main:app --reload --port 4000
```

**Base URLs for WeWeb:**

```
Development: http://localhost:4000
Staging: https://api-staging.example.com
Production: https://api.example.com
```

---

## FIRST PAGE BUILD CHECKLIST

After STEP 5, you'll have:

- [ ] Execution endpoints responding on localhost:4000
- [ ] CORS configured for WeWeb origin
- [ ] Sample intake test data created
- [ ] Backend ready for form submission

Build the first operator screen with:

1. **Form Section**
   - Textarea: "Paste opportunity here"
   - Button: "Create Intake"

2. **Results Section** (after intake created)
   - Display case_id
   - Display classification
   - Display estimated_profit
   - Display recommended_strategy
   - Show task_count

3. **Tasks Section** (after process)
   - List all tasks with sequence
   - Show priority (1=urgent, 10=low)
   - Show instructions

4. **Next Action Section**
   - Call /next-action endpoint
   - Highlight single clear action
   - Show priority + why + how

---

## SUPPORT

**If something fails:**

1. Check server is responding: `curl http://localhost:4000/health`
2. Check logs for errors (server terminal)
3. Verify database file exists: `ls -la valhalla_local.db`
4. Verify environment variables set: `$env: | grep -E "DATABASE|BUILDER|CORS"`
5. Restart server and retry

---

**You are ready. WeWeb can reconnect. Let's build! 🚀**
