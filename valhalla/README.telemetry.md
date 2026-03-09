# Telemetry Hooks (Integrity Ledger) — Pack 9

Endpoints
- POST /telemetry — write an event {event, level, actor, meta}
- GET  /telemetry — list events with filters event, level, actor, limit, offset

Levels: info, warn, error

Middleware
- TelemetryExceptionMiddleware logs unhandled exceptions as http.exception (error).

DB
- Table: integrity_events
- Auto-created by Alembic on deploy.

Usage examples
```bash
# write
curl -s -X POST "$API/telemetry" -H 'Content-Type: application/json' \
  -d '{"event":"builder.apply","level":"info","actor":"heimdall-bot","meta":{"task":"Pack9"}}'

# filter
curl -s "$API/telemetry?level=error&limit=20" | jq .
```
