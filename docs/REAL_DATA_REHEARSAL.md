# REAL DATA REHEARSAL

Generated: 2026-10-08

## Endpoint
- POST /api/completion/shadow/rehearsal/winnipeg

## Intent
Ingest real, publicly accessible Winnipeg-related records for shadow-mode rehearsal with no external side effects.

## Request
```json
{
  "batch_id": "BATCH-SHADOW-REAL-001",
  "limit": 20,
  "mode": "practice",
  "source_ids": ["SRC-WPG-OPEN-DATA", "SRC-CANADA-OPEN-DATA"]
}
```

## Behavior
- Allowed limit: 20 to 50 records.
- Accepts mode `shadow` (normalized to practice) and `practice`/`test`.
- Pulls records from:
  - https://data.winnipeg.ca/api/views.json
  - https://open.canada.ca/data/en/api/3/action/package_search
- Generates deterministic knowledge item IDs for dedupe.
- Stores citation/provenance details in knowledge registry notes/fields.
- No outreach, contract send, or payment effects are executed.

## Response Fields
- batch_id
- mode
- requested_limit
- fetched
- inserted
- duplicates
- blocked
- sources_used

## Safety Notes
- Source governance checks are enforced for live-class sources in practice/test mode.
- Existing anti-injection/poisoned-data/sensitive-data checks remain in completion ingestion paths.

## Executed Evidence
- Run1: fetched=20, inserted=20, duplicates=0, blocked=0.
- Run2 (same batch): fetched=20, inserted=0, duplicates=20, blocked=0.
- Live-mode rejection: status=409 with message "shadow rehearsal is restricted to practice/test modes".
- Inserted distribution: 10 records from `SRC-WPG-OPEN-DATA`, 10 records from `SRC-CANADA-OPEN-DATA`.
- Additional counters (run1): rejected=0, parse_failures=0, source_failures=0.
- Explicit insufficiency counters (run1):
  - VALUATION_CONFIDENCE_LOW=20
  - BUYER_DATA_INSUFFICIENT=20
  - CONTACT_NOT_VERIFIED=20
  - PENDING_HUMAN_REVIEW=20

## Sample Real Records Ingested
- `REAL_SHADOW WWD Rivers, Creeks, and Streams Water Quality Monitoring` (`https://data.winnipeg.ca/d/8vpu-fybf`)
- `REAL_SHADOW Map of Downtown Boundary` (`https://data.winnipeg.ca/d/2df6-k8j2`)
- `REAL_SHADOW Public Services and Procurement Canada federal real estate available for sale to the general public` (`https://open.canada.ca/data/en/dataset/e7a3accb-d419-4d8a-b612-0a601ba4540c`)

## Human Review Evidence Path
- Learning mastery evaluation with high-impact flag and below-gate scores yields `promotion_state=HUMAN_REVIEW_REQUIRED` and `human_review_required=true`.
- Rehearsal knowledge inserts with insufficiency statuses are persisted with `review_status=PENDING_HUMAN_REVIEW`.
