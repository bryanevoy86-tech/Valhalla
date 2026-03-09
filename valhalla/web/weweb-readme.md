# WeWeb import notes (Pack 6)

1. In WeWeb, create variables: `api_base_url` (https Render URL), `accessToken` (JWT).
2. Import each JSON in **Datasources**: `valhalla-api.json`, then the two `*.collection.json` files.
3. Bind dashboard cards: create a collection bound to `metrics.collection.list_metrics`, then map to `MetricCard` (label/value/sub).
4. Capital Intake page: list table bound to `capital_intake.collection.list`, and form bound to `capital_intake.collection.create`.
5. Telemetry page: table widget using `TelemetryTable.json` bound to your telemetry endpoint collection when ready.
