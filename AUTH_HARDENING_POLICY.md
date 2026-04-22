# Auth Hardening Policy

**Date:** April 22, 2026  
**Version:** 1.0

## Overview

This document outlines the authentication and authorization policies for the Universal Deals API.

**Auth Strategy:** Simple session-based auth with optional development token bypass for backward compatibility.

---

## Auth Mechanism

### Required Header
```
X-Session-Token: <session_token>
```

### Configuration
- Environment Variable: `SESSION_TOKEN_DEV`
- When Set: All protected write routes require this token
- When Not Set: Auth is skipped (development mode)
- Builder Key: `X-API-Key` header (separate from session auth)

---

## Route Classification

### 🟢 PUBLIC - Read Only (No Auth Required)

These routes are accessible to everyone for demo/listing purposes:

#### Deals
- `GET /deals` - List all deals
- `GET /deals/{id}` - Get deal details
- `GET /deals/{id}/buyer-matches` - List buyer matches (moved to buyers router)

#### Notifications
- `GET /notifications` - List all notifications
- `GET /audit-log` - View audit trail

#### Buyers (Demo Access)
- `GET /buyers/candidates/list` - List available buyer candidates
- `GET /buyers/{deal_id}/matches` - View matches for a deal

#### Health
- `GET /health` - Health check

---

### 🔒 PROTECTED - Write Operations (Requires Auth)

All mutations require `X-Session-Token` header (if `SESSION_TOKEN_DEV` is configured):

#### Deal Management
- `POST /deals/ui-create` - Create deal from frontend
- `PATCH /deals/{id}` - Update deal (if available)
- `POST /deals/{id}/action` - Change deal status (analyze, hot, dead, pipeline)
- `POST /deals/{id}/analyze` - Run analysis on deal
- `POST /deals/{id}/apply-recommendation` - Apply recommendation
- `PATCH /deals/{id}/disposition` - Update disposition status
- `POST /deals/{id}/notify-event` - Create notification
- `POST /deals/{id}/run-automation` - Run automation rules

#### Buyer Matching
- `POST /buyers/candidates/seed` - Create test buyer candidates
- `POST /buyers/{deal_id}/matches` - Create/update buyer match

#### Notifications
- `POST /notifications/test` - Create test notification

---

## Legacy Routes (Builder Key Auth)

These routes still require the original `X-API-Key: <builder_key>` header:

- `POST /deals` - Create deal via builder API
- Other builder endpoints

---

## Error Responses

### Unauthorized (Missing/Invalid Token)
```
HTTP 401 Unauthorized
{
  "detail": "Unauthorized: X-Session-Token required"
}
```

### Successful Protected Request
Include header:
```bash
curl -X POST http://localhost:4000/deals/123/run-automation \
  -H "X-Session-Token: your-session-token"
```

---

## Configuration Examples

### Development (No Auth Enforcement)
```bash
# No SESSION_TOKEN_DEV set
# All write endpoints accessible without token
# Suitable for local development
```

### Production (Auth Required)
```bash
export SESSION_TOKEN_DEV="prod-session-token-abc123"
# All write endpoints require X-Session-Token header
# Session tokens must match configured value
```

---

## Migration Notes

- **Backward Compatible**: Existing routes unchanged
- **Backward Compatible**: Builder key auth still works
- **New Routes**: All new write endpoints protected by default
- **Development**: Set `SESSION_TOKEN_DEV=""` to disable auth (local dev only)
- **Frontend**: Update to send `X-Session-Token` header on mutations

---

## Frontend Integration

### JavaScript Example
```javascript
const sessionToken = "your-session-token";

// Protected endpoint
fetch("http://localhost:4000/deals/123/run-automation", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-Session-Token": sessionToken,
  },
  body: JSON.stringify({ /* payload */ })
})
.then(r => r.json())
.then(data => console.log(data));
```

### Read-Only Endpoint (No Token Needed)
```javascript
// Public read
fetch("http://localhost:4000/deals")
  .then(r => r.json())
  .then(data => console.log(data));
```

---

## Render Deployment

No changes required for Render. Just set the environment variable:

```bash
SESSION_TOKEN_DEV=your-production-token
```

Or leave unset for development deployments.

---

## Summary

| Layer | Public Reads | Protected Writes | Builder Key |
|-------|--------------|------------------|-------------|
| Deals | ✅ List/Get | 🔒 Requires Session Token | Legacy auth |
| Buyers | ✅ List candidates | 🔒 Requires Session Token | - |
| Notifications | ✅ List | 🔒 Requires Session Token | - |
| Audit | ✅ View | N/A (read-only) | - |

---

## Next Steps

1. Set `SESSION_TOKEN_DEV` environment variable in production
2. Update frontend to send `X-Session-Token` header on mutations
3. Test with dev token first
4. Monitor audit logs for failed auth attempts
