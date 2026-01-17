# Pack 18: Advanced Data Encryption & Privacy

This pack adds Fernet-based encryption for sensitive data, exposing simple encrypt/decrypt APIs and a small UI.

## Endpoints
- POST `/api/encryption/encrypt` — body `{ "data": "..." }` returns `{ data, encrypted, encryption_key }`
- POST `/api/encryption/decrypt` — body `{ "encrypted_data": "...", "encryption_key": "..." }` returns plaintext as a string

## Quick test (PowerShell)
```powershell
$API = "https://<your-render-service>.onrender.com"

# Encrypt
$enc = Invoke-RestMethod -Method Post -Uri "$API/api/encryption/encrypt" -ContentType 'application/json' -Body (@{ data = 'Sensitive data' } | ConvertTo-Json)
$enc | ConvertTo-Json -Depth 4

# Decrypt
$dec = Invoke-RestMethod -Method Post -Uri "$API/api/encryption/decrypt" -ContentType 'application/json' -Body (@{ encrypted_data = $enc.data; encryption_key = $enc.encryption_key } | ConvertTo-Json)
$dec
```

## UI
- GET `/api/ui-dashboard/encryption-dashboard-ui`

## Notes
- This is a minimal surface. For production: persist keys securely (e.g., KMS/Secrets Manager), implement key rotation, restrict access, and add integrity checks.
- The router is imported with a guard in `services/api/main.py` to avoid startup failures if deps are missing.
