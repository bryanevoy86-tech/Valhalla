# FINAL ENDPOINT INVENTORY

## VA Intake
```
POST   /api/va-intake/lead
GET    /api/va-intake/leads
GET    /api/va-intake/leads/{id}
GET    /api/va-intake/approvals/pending
POST   /api/va-intake/approvals/{id}/approve
POST   /api/va-intake/approvals/{id}/deny
POST   /api/va-intake/leads/{id}/convert-to-deal
GET    /api/va-intake/leads/{id}/deal
GET    /api/va-intake/leads/{id}/audit
```

## Go Live
```
GET /api/go-live/status
```

## Messaging
```
POST /api/heimdall/draft-seller-message/{lead_id}
POST /api/heimdall/create-buyer-packet/{deal_id}
```

## Reports
```
GET /api/reports/va-leads-summary
GET /api/reports/approval-summary
GET /api/reports/eia-monthly-summary
```

## Dev (Testing Only)
```
POST /api/dev/seed-va-test-data
POST /api/dev/clear-test-data
GET  /api/dev/duplicate-check
```

## Status
- **Total Endpoints**: 15+
- **Testing Status**: 7/7 PASSING ✅
- **Backend Freeze Commit**: 908d481
- **Ready for WeWeb**: YES
