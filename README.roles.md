# Pack 16: Enhanced User Role Permissions

Adds a simple RBAC surface for role → permissions mapping and a small UI to view permissions.

## Endpoints
- `GET /api/roles/admin`
- `GET /api/roles/editor`
- `GET /api/roles/viewer`

## Quick test (PowerShell)
```powershell
$API = "https://<your-render-service>.onrender.com"
Invoke-RestMethod -Method Get -Uri "$API/api/roles/admin" | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Get -Uri "$API/api/roles/editor" | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Get -Uri "$API/api/roles/viewer" | ConvertTo-Json -Depth 4
```

## UI
- `GET /api/ui-dashboard/role-permissions-dashboard-ui` — HTML page that fetches `/api/roles/{role}` and renders permissions

## Notes
- This is intentionally minimal; to persist roles/permissions and manage assignment, add models and tables, then read from DB in RolesService.
