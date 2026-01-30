#!/bin/sh
# Cron job entrypoint for daily ops email
# This script runs the daily ops email sender

set -e

echo "==> Valhalla Daily Ops Cron Job"
echo "==> Working directory: $(pwd)"
echo "==> Time: $(date)"
echo "==> CRON_MODE: ${CRON_MODE}"

# Make sure we're in the right directory
cd /app/services/api

# If CRON_MODE=daily_ops, run the email sender
if [ "$CRON_MODE" = "daily_ops" ]; then
    echo "==> Running daily ops email builder..."
    python -m app.jobs.daily_ops_email
    exit $?
else
    echo "==> CRON_MODE not set to 'daily_ops', exiting."
    exit 0
fi
