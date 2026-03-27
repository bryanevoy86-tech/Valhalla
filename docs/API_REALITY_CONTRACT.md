# API REALITY CONTRACT

**Date:** March 26, 2026  
**Purpose:** Document ACTUAL observed API behavior from live system  
**Method:** TestClient probing of running FastAPI app

---

## OBSERVED API ENDPOINTS

### ✅ WORKING ENDPOINTS

#### 1. GET /health
```
Status: 200 OK
Response:
{
  "status": "ok",
  "heimdall": "online"
}
```
- Health check is working
- Heimdall is reported as "online" but endpoints don't respond

---

#### 2. POST /api/leads (exists but requires fields)
```
Status: 422 VALIDATION ERROR
Required fields: name, email, phone, source
Example response:
{
  "type": "https://valhalla/errors/validation",
  "title": "Validation error",
  "status": 422,
  "detail": "One or more fields failed validation.",
  "extra": {
    "errors": [
      {"type": "missing", "loc": ["body", "name"], ...},
      {"type": "missing", "loc": ["body", "email"], ...},
      {"type": "missing", "loc": ["body", "phone"], ...},
      {"type": "missing", "loc": ["body", "source"], ...}
    ]
  }
}
```
- Lead creation requires: name, email, phone, source (not deal fields)
- This is NOT the deals endpoint

---

### ❌ DOCUMENTED BUT NOT FOUND

| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /api/deals` | 404 | Not Found - deals router disabled |
| `POST /api/deals` | 404 | Deal creation route doesn't exist |
| `POST /api/heimdall/deals/{id}/analyze` | 404 | **CRITICAL: Heimdall analyze not found** |
| `POST /api/heimdall/deals/{id}/advance-stage` | 404 | **CRITICAL: Heimdall stage advance not found** |
| `GET /api/audit/deals/{id}` | 404 | Audit endpoint not found |
| `GET /api/dashboard/pipeline` | 404 | Dashboard pipeline not found |
| `GET /api/dashboard/deals/{id}/timeline` | 404 | Dashboard timeline not found |

---

## ROUTE REGISTRATION STATUS (from app logs)

```
[app.main] Heimdall activation module imported
[app.main] Skipping buyers router: No module named 'rapidfuzz'
[app.main] Skipping deals router: Table 'deals' is already defined for this MetaData instance
```

**Finding:** 
- Heimdall module was **imported** ✅
- Heimdall module was **NOT registered** in router list ❌
- Buyers router **skipped** due to missing `rapidfuzz` dependency ❌
- Deals router **disabled** due to SQLAlchemy table conflicts ❌

---

## ERROR HANDLING

### Response Format for 404s
```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Not Found",
  "instance": "http://testserver/api/...",
  "correlation_id": "...",
  "extra": null
}
```

### Error Handling Quality
- ✅ No 500 errors for basic operations
- ✅ Structured 404 responses (not silently ignored)
- ✅ 422 validation errors are properly formatted
- ✅ No malformed responses observed

---

## TEST EXECUTION SUMMARY

```
Platform: Windows Python 3.13.7, pytest-9.0.2
Total Tests: 15
Passed: 15
Failed: 0
Errors: 0
Warnings: 280 (mostly deprecation warnings)

Test Groups:
✅ API Boot and Baseline (3/3 passed)
✅ Deal Visibility (2/2 passed - both 404 as expected)
✅ Heimdall Analysis (2/2 passed - 404 detected)
✅ Heimdall Stage Advancement (2/2 passed - 404 detected)
✅ Audit and Dashboard (3/3 passed - all 404)
✅ Persistence (1/1 passed)
✅ Error Handling (2/2 passed)
```

---

## KEY FINDINGS

### What the System Actually Does
1. ✅ App boots and initializes
2. ✅ Health endpoint works
3. ✅ Lead intake exists (requires name, email, phone, source)
4. ✅ Error handling is structured (no 500s on bad input)
5. ❌ Deals management routes are disabled
6. ❌ Heimdall routes do NOT exist
7. ❌ Audit trail is NOT available as documented
8. ❌ Dashboard is NOT available

### Root Causes
1. **Missing dependency:** `rapidfuzz` module not installed (buyers router skipped)
2. **Schema conflict:** `deals` table defined twice, causing SQLAlchemy error
3. **Router not registered:** Heimdall module imported but router not added to registry
4. **Integration incomplete:** Core pipeline endpoints are not exposed

---

## DOCUMENTATION DRIFT

| Claim in Docs | Actual Behavior | Status |
|---------------|-----------------|--------|
| "Heimdall analyze endpoint works" | Returns 404 | ❌ BROKEN |
| "Stage advancement logic enforced" | Endpoint not found | ❌ BROKEN |
| "Audit trail is queryable" | Returns 404 | ❌ BROKEN |
| "Dashboard pipeline visible" | Returns 404 | ❌ BROKEN |
| "System is operational" | Health OK but core routes missing | ⚠️ PARTIAL |

---

## CONCLUSION

The **documented Heimdall system does not exist in the live API**.

The code files exist:
- `services/api/app/services/heimdall_service.py` ✅ (created)
- `services/api/app/routers/heimdall.py` ✅ (created)
- `services/api/app/main.py` ❌ (router registration may not have worked)

But the **HTTP endpoints are not accessible** from the running system.

This is a **registration/wiring problem**, not a code logic problem.
