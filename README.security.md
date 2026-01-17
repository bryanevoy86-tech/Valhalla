# Pack 17: Enhanced Security Features (2FA, Rate Limiting)

This pack adds a basic surface for two-factor auth (2FA) and rate limiting. It includes:
- Endpoints to generate and verify a 2FA token (placeholder verification)
- Endpoint to check rate-limit info (placeholder counts)
- Simple Security Dashboard UI

Note: This is a lightweight foundation. It does not persist 2FA secrets/tokens or enforce limits; replace placeholders with real storage and counters.

## Endpoints
- POST `/api/security/generate-2fa` — accepts `user_id` via query or JSON body
- POST `/api/security/verify-2fa` — accepts `user_id` and `token` via query or JSON body
- GET `/api/security/rate-limit?user_id=<id>`

## Quick test (PowerShell)
```powershell
$API = "https://<your-render-service>.onrender.com"

# Generate 2FA token (placeholder response)
Invoke-RestMethod -Method Post -Uri "$API/api/security/generate-2fa?user_id=user_123" | ConvertTo-Json -Depth 4

# Verify 2FA token (placeholder validation)
Invoke-RestMethod -Method Post -Uri "$API/api/security/verify-2fa?user_id=user_123&token=123456" | ConvertTo-Json -Depth 4

# Check rate limit
Invoke-RestMethod -Method Get -Uri "$API/api/security/rate-limit?user_id=user_123" | ConvertTo-Json -Depth 4
```

## UI
- `GET /api/ui-dashboard/security-dashboard-ui` — interacts with the `/api/security/*` endpoints

## Implementation notes
- 2FA uses `pyotp` for key generation; real verification flow should store a per-user secret and validate tokens via `pyotp.TOTP(secret).verify(token)`.
- Rate limiting is a stub; consider libraries like `slowapi` or infrastructure-level (proxy/WAF) limits.
- The router import is guarded in `services/api/main.py` to avoid crashes if dependencies are missing; ensure `pyotp` is installed (added to `services/api/requirements.txt`).