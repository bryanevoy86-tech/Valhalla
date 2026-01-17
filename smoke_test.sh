#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# Valhalla / Heimdall Go-Live Smoke Test (Canada-wide wholesale)
# ------------------------------------------------------------
# What it validates end-to-end:
# 1) Governance runbook status
# 2) OfferPolicy enabled for a province/market
# 3) MarketPolicy effective rules (contact windows/channels)
# 4) Create Lead+Deal flow (lead → deal_brief → backend_deal)
# 5) Auto follow-up ladder creation + due tasks
# 6) Offer computation (sandbox exec)
# 7) Buyer match attempt/result KPIs (if buyers exist)
# 8) Notification preparation metadata (no sending)
#
# Requirements:
# - API running
# - DB migrated
# - jq installed (recommended)
#
# Usage:
#   BASE_URL="http://localhost:8000" ./smoke_test.sh
#   BASE_URL="https://your-domain" TOKEN="..." ./smoke_test.sh
#   ./smoke_test.sh http://localhost:8000  (pass as argument)
# ------------------------------------------------------------

BASE_URL="${1:-${BASE_URL:-http://localhost:8000}}"
TOKEN="${TOKEN:-}"
AUTH_HEADER=()
if [[ -n "${TOKEN}" ]]; then
  AUTH_HEADER=(-H "Authorization: Bearer ${TOKEN}")
fi

HJSON=(-H "Content-Type: application/json" "${AUTH_HEADER[@]}")

echo "BASE_URL=${BASE_URL}"
echo

need_jq=1
command -v jq >/dev/null 2>&1 || need_jq=0
if [[ "$need_jq" -eq 0 ]]; then
  echo "⚠️  jq not found. Script will still run but parsing ids may fail."
fi

# Helpers
curl_json () {
  curl -sS "${HJSON[@]}" "$@"
}
curl_any () {
  curl -sS "${AUTH_HEADER[@]}" "$@"
}

echo "1) Runbook status"
curl_any "${BASE_URL}/api/governance/runbook/status" | ( [[ "$need_jq" -eq 1 ]] && jq '.' || cat )
echo

# Choose a test market: Ontario / Toronto (market inference should produce TORONTO if region contains it)
PROVINCE="ON"
MARKET="TORONTO"

echo "2) Enable OfferPolicy for ${PROVINCE}/${MARKET} (so offer compute will succeed)"
curl_any -X POST "${BASE_URL}/api/deals/offers/policies/upsert?province=${PROVINCE}&market=${MARKET}&enabled=true&max_arv_multiplier=0.70&default_assignment_fee=10000&default_fees_buffer=2500&changed_by=bryan&reason=smoke_test" \
  | ( [[ "$need_jq" -eq 1 ]] && jq '.' || cat )
echo

echo "3) Confirm MarketPolicy effective rules for ${PROVINCE}/${MARKET}"
curl_any "${BASE_URL}/api/governance/market/effective?province=${PROVINCE}&market=${MARKET}" | ( [[ "$need_jq" -eq 1 ]] && jq '.' || cat )
echo

echo "4) Create Lead+Deal flow (lead → deal brief → backend deal)"
# IMPORTANT: This payload must match your existing FlowLeadToDealRequest schema.
# If your schema differs, only edit the JSON below—everything else can remain.
FLOW_PAYLOAD='{
  "lead": {
    "source": "smoke_test",
    "phone": "+14035550123",
    "email": "seller@example.com",
    "name": "Test Seller",
    "notes": "Smoke test lead"
  },
  "deal": {
    "region": "Toronto, ON, Canada",
    "price": 450000,
    "arv": 650000,
    "repairs": 35000,
    "offer": 0,
    "mao": 0,
    "roi_note": "smoke_test"
  },
  "match_settings": {
    "match_buyers": true,
    "min_match_score": 0.5,
    "max_results": 10
  }
}'

FLOW_RES="$(curl_json -X POST "${BASE_URL}/api/flow/lead-to-deal" -d "${FLOW_PAYLOAD}")"
echo "$FLOW_RES" | ( [[ "$need_jq" -eq 1 ]] && jq '.' || cat )
echo

if [[ "$need_jq" -eq 1 ]]; then
  LEAD_ID="$(echo "$FLOW_RES" | jq -r '.lead.id // .lead_id // empty')"
  DEAL_BRIEF_ID="$(echo "$FLOW_RES" | jq -r '.deal_brief.id // .deal_brief_id // empty')"
  BACKEND_DEAL_ID="$(echo "$FLOW_RES" | jq -r '.backend_deal.id // .backend_deal_id // empty')"
  echo "Parsed IDs:"
  echo "  lead_id=${LEAD_ID:-<not found>}"
  echo "  deal_brief_id=${DEAL_BRIEF_ID:-<not found>}"
  echo "  backend_deal_id=${BACKEND_DEAL_ID:-<not found>}"
  echo
fi

echo "5) Check follow-up ladder due tasks (should exist immediately)"
curl_any "${BASE_URL}/api/followups/due?limit=20" | ( [[ "$need_jq" -eq 1 ]] && jq '.' || cat )
echo

echo "6) Offer compute (sandbox) for ${PROVINCE}/${MARKET}"
# comps_json/assumptions_json are optional. Keep it simple.
curl_any -X POST "${BASE_URL}/api/deals/offers/compute?province=${PROVINCE}&market=${MARKET}&arv=650000&repairs=35000&correlation_id=smoke_test_offer" \
  | ( [[ "$need_jq" -eq 1 ]] && jq '.' || cat )
echo

echo "7) Buyer liquidity score snapshot (even if empty, should return a node/score)"
curl_any "${BASE_URL}/api/buyers/liquidity/score?province=${PROVINCE}&market=${MARKET}&property_type=SFR" | ( [[ "$need_jq" -eq 1 ]] && jq '.' || cat )
echo

echo "8) Prepare notifications metadata (NO sending; just payload generation)"
if [[ "$need_jq" -eq 1 && -n "${BACKEND_DEAL_ID:-}" ]]; then
  NOTIFY_PAYLOAD="$(jq -n --argjson id "${BACKEND_DEAL_ID}" '{"backend_deal_id": $id, "target": "seller", "channel": "SMS"}')"
else
  # fallback: you can manually paste backend_deal_id if jq isn't installed
  NOTIFY_PAYLOAD='{"backend_deal_id": 1, "target": "seller", "channel": "SMS"}'
fi

curl_json -X POST "${BASE_URL}/api/flow/notifications" -d "${NOTIFY_PAYLOAD}" \
  | ( [[ "$need_jq" -eq 1 ]] && jq '.' || cat )
echo

echo "9) Governance snapshots (optional but useful)"
echo "- Risk policies:"
curl_any "${BASE_URL}/api/governance/risk/policies" | ( [[ "$need_jq" -eq 1 ]] && jq '.' || cat )
echo
echo "- Heimdall charter policies:"
curl_any "${BASE_URL}/api/governance/heimdall/policies" | ( [[ "$need_jq" -eq 1 ]] && jq '.' || cat )
echo
echo "- Regression state:"
curl_any "${BASE_URL}/api/governance/regression/state" | ( [[ "$need_jq" -eq 1 ]] && jq '.' || cat )
echo

echo "✅ Smoke test complete."
echo "If any step failed, paste the failing response and I'll tell you exactly what to adjust."
