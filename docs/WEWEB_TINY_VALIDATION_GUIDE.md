# WeWeb Tiny Validation Guide

**Purpose**: Validate that WeWeb can communicate with Render backend and perform basic authentication/data flow.

**Scope**: Minimal UI focused on testing backend contract, NOT a full application.

---

## Setup

### 1. Create WeWeb Application

1. Log into WeWeb at: https://www.weweb.io/
2. Create new app or use existing test app
3. Set API base URL variable

### 2. WeWeb Variables to Create

Create these variables in WeWeb App Settings → Variables:

```
apiBaseUrl              (String)  → https://YOUR-RENDER-API.onrender.com
emailInput              (String)  → test user email
passwordInput           (String)  → test user password
accessToken             (String)  → token from login
currentUser             (Object)  → user data from /me
smokeStatus             (Object)  → smoke check response
systemStatus            (Object)  → system status response
goLiveState             (Object)  → go-live state response
dashboardData           (Object)  → dashboard response
nextActions             (Object)  → next actions response
reportsSummary          (Object)  → reports summary response
```

---

## API Workflow

### 1. Smoke Check (No Auth)

**Action**: Click button or on-page-load

```
Method:  GET
URL:     {{apiBaseUrl}}/api/weweb/smoke
Headers: (none)
Success: Set smokeStatus = response
```

**Expected Response**:
```json
{
  "ok": true,
  "status": "healthy",
  "timestamp": "2026-06-27T..."
}
```

**WeWeb Action**: 
- Display smokeStatus.ok (should be true)
- Display smokeStatus.status (should be "healthy")

---

### 2. Login

**Action**: "Login" button click

**Inputs**: 
- `emailInput` (user email)
- `passwordInput` (user password)

```
Method:  POST
URL:     {{apiBaseUrl}}/api/weweb/login
Headers: Content-Type: application/json
Body:    {
  "email": "{{emailInput}}",
  "password": "{{passwordInput}}"
}
Success: Set accessToken = response.access_token
```

**CRITICAL**: Token path is `response.access_token` (not `response.token`)

**Expected Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

### 3. Current User

**Action**: After successful login

```
Method:  GET
URL:     {{apiBaseUrl}}/api/weweb/me
Headers: Authorization: Bearer {{accessToken}}
Success: Set currentUser = response.user
```

**Expected Response**:
```json
{
  "ok": true,
  "user": {
    "email": "admin@valhalla.local",
    "role": "owner"
  }
}
```

---

### 4. System Status

**Action**: After login

```
Method:  GET
URL:     {{apiBaseUrl}}/api/jarvis/system-status
Headers: Authorization: Bearer {{accessToken}}
Success: Set systemStatus = response
```

**Expected Response**:
```json
{
  "ok": true,
  "mode": "normal",
  "heimdall_status": {...}
}
```

---

### 5. Go-Live State

**Action**: After login

```
Method:  GET
URL:     {{apiBaseUrl}}/governance/go-live/state
Headers: Authorization: Bearer {{accessToken}}
Success: Set goLiveState = response
```

**Expected Response**:
```json
{
  "go_live_enabled": false,
  "kill_switch_engaged": false,
  "changed_by": null,
  "reason": null,
  "updated_at": "2026-06-27T..."
}
```

---

### 6. Dashboard (Optional)

**Action**: After login

```
Method:  GET
URL:     {{apiBaseUrl}}/api/jarvis/dashboard
Headers: Authorization: Bearer {{accessToken}}
Success: Set dashboardData = response
```

**Expected Response**: Raw JSON (display as code block for now)

---

### 7. Next Actions (Optional)

**Action**: After login

```
Method:  GET
URL:     {{apiBaseUrl}}/api/jarvis/next-actions
Headers: Authorization: Bearer {{accessToken}}
Success: Set nextActions = response.items or response
```

**Expected Response**: Array or object

---

### 8. Reports Summary

**Action**: After login

```
Method:  GET
URL:     {{apiBaseUrl}}/reports/summary
Headers: Authorization: Bearer {{accessToken}}
Success: Set reportsSummary = response
```

**Expected Response**: Raw JSON (display as code block for now)

---

## Tiny UI Layout

### Section 1: Smoke Check (No Auth Required)

- **Component**: Button "Check Backend Health"
- **Action**: Call Smoke Check API
- **Display**:
  - `Smoke Status: {{smokeStatus.status}}`
  - Color: Green if ok=true, Red if false

### Section 2: Login Form

- **Email Input**: Bind to `emailInput`
- **Password Input**: Bind to `passwordInput`
- **Login Button**: 
  - Disabled until both fields filled
  - Call Login API
  - On success: Show "✅ Logged in as {{currentUser.email}}"
  - On error: Show error message
  - Show token preview: `Token: {{accessToken.substring(0,30)}}...`

### Section 3: Current User Card

- Display after login:
  ```
  Email: {{currentUser.email}}
  Role: {{currentUser.role}}
  ```

### Section 4: System Status Card

- Display after login:
  ```
  Status: {{systemStatus.ok}}
  Mode: {{systemStatus.mode}}
  ```

### Section 5: Go-Live Banner

- Display after login:
  - Color GREEN if `goLiveState.go_live_enabled = true`
  - Color RED if `goLiveState.kill_switch_engaged = true`
  - Color YELLOW if neither
  - Text: Show `go_live_enabled` and `kill_switch_engaged` status

### Section 6: Dashboard Preview (JSON)

- Display after login:
  - Raw JSON code block: `{{JSON.stringify(dashboardData, null, 2)}}`

### Section 7: Next Actions List

- Display after login:
- If `nextActions` is array:
  - Repeat over items
  - Display each action as list item
- If empty:
  - Show "No pending actions"

### Section 8: Reports Summary (JSON)

- Display after login:
  - Raw JSON code block: `{{JSON.stringify(reportsSummary, null, 2)}}`

---

## Acceptance Criteria

- ✅ Smoke check returns 200 and ok=true
- ✅ Login returns 200 and access_token is present
- ✅ Token stored in accessToken variable
- ✅ /me returns 200 and currentUser has email and role
- ✅ /api/jarvis/system-status returns 200
- ✅ /governance/go-live/state returns 200 with expected schema
- ✅ /api/jarvis/dashboard returns 200 and displays as JSON
- ✅ /api/jarvis/next-actions returns 200
- ✅ /reports/summary returns 200
- ✅ All authenticated endpoints use Bearer token correctly
- ✅ No CORS errors in browser console
- ✅ No auth header/token hardcoded in app (variables only)

---

## Testing Checklist

Before declaring tiny validation complete:

- [ ] Backend Render URL confirmed working (health endpoint)
- [ ] Login with test credentials works
- [ ] Token is stored and used for subsequent requests
- [ ] All required endpoints return 200
- [ ] No CORS errors
- [ ] UI displays all response data correctly
- [ ] WeWeb variables are properly bound
- [ ] Token expires/refresh behavior tested (optional for tiny)

---

## Notes

- **Tiny scope**: This is NOT the full Valhalla UI. It's a testing harness.
- **No styling required**: Focus on functionality and data flow.
- **JSON display OK**: For now, showing dashboardData and reportsSummary as raw JSON is acceptable.
- **Next Phase**: Once tiny validation passes, move to Heimdall Background Builder V0.

---

Generated: Valhalla Render Deploy + WeWeb Validation Pack
