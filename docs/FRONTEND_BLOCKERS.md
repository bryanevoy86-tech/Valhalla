# FRONTEND BLOCKERS

Generated: 2026-09-28

## Active Blocker
- ID: PRODUCTION_AUTH_CREDENTIAL_REQUIRED
- Class: EXTERNAL_OWNER_ACTION_REQUIRED
- Description: Full live authenticated chain and WeWeb Preview auth verification require secure credential execution.

## Evidence
- Live production OpenAPI includes:
  - `/api/weweb/login`
  - `/api/weweb/me`
  - `/api/weweb/logout`
  - `/api/weweb/refresh`
  - `/api/weweb/smoke`
  - `/api/weweb/admin/reset-owner-password`
- Live deployment identity still reports:
  - `/deployment-marker`: env-derived commit `9cc0dc4324a4940e3e748e0b31ebc20f8096486e`
  - `/admin/build/info`: matching env-derived `git_sha`

## Impact
- Auth route contract and deployment parity are now available in production.
- Remaining gap is secure execution of full authenticated proof chain.

## Latest Verification
- Source with `/api/weweb/logout` and `/api/weweb/refresh` is on `origin/main` and deployed with runtime identity parity commit `9cc0dc4`.
- Live runtime probe confirms both routes are present in `GET /openapi.json`.
- Live runtime now reports parity commit `9cc0dc4` through both identity endpoints.

## Secure Credential Setup (Owner Action)
Use local shell environment variables only:

```
$env:VALHALLA_TEST_EMAIL = "owner-or-test-account@example.com"
$secure = Read-Host "Enter production-safe test password" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
  $env:VALHALLA_TEST_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}
```

Confirm variable presence only (no value echo):

```
Write-Output ("VALHALLA_TEST_EMAIL_SET=" + [bool]$env:VALHALLA_TEST_EMAIL)
Write-Output ("VALHALLA_TEST_PASSWORD_SET=" + [bool]$env:VALHALLA_TEST_PASSWORD)
```

## Commit Parity Snapshot
- EXPECTED_COMMIT: `9cc0dc4324a4940e3e748e0b31ebc20f8096486e`
- LIVE_COMMIT_OR_BUILD: `9cc0dc4324a4940e3e748e0b31ebc20f8096486e`
- MATCH: `YES`
- CAUSE_IF_KNOWN: N/A

## Unblock Condition
- Execute secure production login chain and WeWeb Preview parity checks.
- Record PASS/FAIL evidence for login -> me -> refresh -> logout -> post-logout persistence.