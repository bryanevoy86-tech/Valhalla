#!/bin/sh
# Alternative daily ops cron trigger via HTTP endpoint
# This calls the real endpoint instead of the Python module directly
# Useful for avoiding auth issues and testing the endpoint

set -e

echo "==> Valhalla Daily Ops HTTP Trigger"
echo "==> Time: $(date)"
echo "==> Service URL: ${VALHALLA_SERVICE_URL}"

# Get the service URL (default to API if not set)
SERVICE_URL="${VALHALLA_SERVICE_URL:-http://localhost:8000}"
SERVICE_URL="${SERVICE_URL%/}"  # Remove trailing slash if present

# Optional CRON_TOKEN for authenticated trigger
CRON_TOKEN="${CRON_TOKEN:-}"

echo "==> Calling POST ${SERVICE_URL}/api/notify/daily-ops-email"

# Build curl command
if [ -n "$CRON_TOKEN" ]; then
    # With auth token
    curl -X POST \
        -H "Authorization: Bearer ${CRON_TOKEN}" \
        -H "Content-Type: application/json" \
        "${SERVICE_URL}/api/notify/daily-ops-email" \
        -w "\nHTTP Status: %{http_code}\n"
else
    # Without auth (if endpoint is public or open during cron window)
    curl -X POST \
        -H "Content-Type: application/json" \
        "${SERVICE_URL}/api/notify/daily-ops-email" \
        -w "\nHTTP Status: %{http_code}\n"
fi

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Daily ops email trigger successful"
else
    echo "❌ Daily ops email trigger failed (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
