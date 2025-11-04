#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8000/api/v1}"

echo "Seeding admin user…"
curl -sS -X POST "$API/users" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme","full_name":"Admin","role":"admin"}' \
  | jq -r '.id? // "ok"' || true
echo "Done."
