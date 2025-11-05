#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8000/api/v1}"

echo "Logging in…"
curl -sS -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme"}' \
  | jq .
