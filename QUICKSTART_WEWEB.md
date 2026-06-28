# Quick Start: Valhalla Backend with WeWeb Integration

## One-Command Backend Start

```powershell
cd d:\dev
$env:DATABASE_URL = "sqlite:///valhalla_test.db"
$env:VALHALLA_OWNER_USERNAME = "admin"
$env:VALHALLA_OWNER_PASSWORD = "admin-local-only"
$env:VALHALLA_JWT_SECRET = "local-dev-secret-key"
python start.py
```

Backend will start on `http://localhost:8000`

## Test WeWeb Auth Flow

### 1. Check Service is Running
```bash
curl http://localhost:8000/api/weweb/smoke
# Response: {"ok":true,"message":"WeWeb auth bridge live"}
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/weweb/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin","password":"admin-local-only"}'

# Response: 
# {
#   "ok": true,
#   "access_token": "eyJ...",
#   "token_type": "bearer",
#   "user": {"email": "admin", "role": "owner"}
# }
```

### 3. Get Current User (with token)
```bash
curl -H "Authorization: Bearer <token from login>" \
  http://localhost:8000/api/weweb/me

# Response:
# {"ok":true,"user":{"email":"admin","role":"owner"}}
```

### 4. Check Go-Live State
```bash
curl http://localhost:8000/governance/go-live/state

# Response:
# {
#   "go_live_enabled": false,
#   "kill_switch_engaged": false,
#   "changed_by": null,
#   "reason": null,
#   "updated_at": "2026-06-28T..."
# }
```

## Key Endpoints

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `POST /api/weweb/login` | Login with email/password | None |
| `GET /api/weweb/me` | Get current user info | Bearer token |
| `GET /api/weweb/smoke` | Health check | None |
| `GET /governance/go-live/state` | Get go-live state | None |
| `GET /health` | Backend health | None |
| `GET /api/jarvis/system-status` | System status | None |

## Credentials (Local Dev)

- **Username**: `admin`
- **Password**: `admin-local-only`
- **Email**: `admin@valhalla.local`

## Environment Variables

```bash
# Required
DATABASE_URL="sqlite:///valhalla_test.db"
VALHALLA_OWNER_USERNAME="admin"
VALHALLA_OWNER_PASSWORD="admin-local-only"
VALHALLA_JWT_SECRET="local-dev-secret-key"

# Optional
VALHALLA_AUTH_ENABLED="true"  # Default: true
VALHALLA_TOKEN_TTL_SECONDS="3600"  # Default: 1 hour
```

## Files Modified

- `services/api/app/models/__init__.py` — Added GoLiveState import
- `alembic/versions/20260527_add_go_live_state.py` — Migration for go_live_state table

## Documentation

- [RUNTIME_CONTRACT_REPAIR_RESULTS.md](RUNTIME_CONTRACT_REPAIR_RESULTS.md) — Full details
- [WEWEB_READINESS_TRUTH.md](WEWEB_READINESS_TRUTH.md) — Integration status
- [ALEMBIC_SINGLE_HEAD_REPAIR_RESULTS.md](ALEMBIC_SINGLE_HEAD_REPAIR_RESULTS.md) — Migration fixes

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (requires 3.11+)
- Check venv: `. .venv/bin/activate`
- Check DATABASE_URL is set: `echo $env:DATABASE_URL`

### 404 on `/api/weweb/*`
- Ensure VALHALLA_OWNER_USERNAME is set
- Check backend logs for router load errors
- Verify `services/api/app/routers/weweb_auth.py` exists

### 500 on `/governance/go-live/state`
- Check that go_live_state table exists
- Verify database file is accessible
- Check backend logs for SQL errors

## Status

✅ All endpoints operational  
✅ Authentication flow verified  
✅ Database migrations fixed  
✅ Ready for WeWeb integration

See [RUNTIME_CONTRACT_REPAIR_RESULTS.md](RUNTIME_CONTRACT_REPAIR_RESULTS.md) for full details.
