# VALHALLA LAUNCH CORE CHECKLIST

## Must Be True Before Go Button
- [x] launch_core_only is TRUE
- [x] enable_eia_tracking is TRUE
- [x] require_eia_compliance is TRUE
- [x] route count remains reduced
- [x] /health returns 200
- [x] /docs returns 200
- [x] /api/launch/status returns 200
- [x] /api/go-button/status returns 200
- [x] /api/eia/status returns 200
- [x] EIA compliance risk is not HIGH
- [x] Missing receipts = 0
- [x] Unclassified income = 0
- [x] Owner draw = false in protected mode

## Soft-Live Proof Flows
- [x] lead route responds
- [x] deal route responds
- [x] offer / contract route responds
- [x] buyer route responds
- [x] audit route responds
- [x] launch wrapper prunes non-core routes
- [x] EIA packet can be built

## Not Yet Allowed
- [x] payments (disabled)
- [x] banking (disabled)
- [x] accounting (disabled)
- [x] finops (disabled)
- [x] heimdall autonomy (disabled)
