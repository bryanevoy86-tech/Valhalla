#!/usr/bin/env bash
# Grab current logs & spans from the API and save locally.
# Usage: ./pull-observability.sh http://localhost:8000

set -euo pipefail
BASE="${1:-http://localhost:8000}"
STAMP=$(date +%Y%m%d-%H%M%S)

echo ">> Pulling span export ..."
curl -fsSL "$BASE/admin/observability/spans/export" -o "traces-$STAMP.jsonl" || echo "No traces file yet."

echo ">> Listing log files ..."
curl -fsSL "$BASE/admin/logs/list" -o "logs-list-$STAMP.json" || { echo "List failed"; exit 0; }

DEFAULT_PATH=$(jq -r '.path' "logs-list-$STAMP.json")
FILES=$(jq -r '.files[].file' "logs-list-$STAMP.json")

if [ -z "$FILES" ]; then
  echo "No log files reported by admin endpoint."
  exit 0
fi

for f in $FILES; do
  echo ">> Download $f"
  curl -fsSL "$BASE/admin/logs/get?file=$(printf "%s" "$f" | jq -sRr @uri)" -o "$f"
done

echo "Done. Saved alongside this script."
