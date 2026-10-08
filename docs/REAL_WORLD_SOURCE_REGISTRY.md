# REAL WORLD SOURCE REGISTRY

Generated: 2026-10-08

## Scope
This document describes source-governance fields required for shadow rehearsal with real public data.

## Source Registry Fields
Added on source registry records:
- permission_status
- license_status
- rights_statement_url
- robots_policy
- trust_tier
- provenance_method
- freshness_sla_hours
- last_verified_at
- governance_status
- shadow_approved

## Shadow Eligibility Rules
For live-class sources used in practice/test mode:
- permission_status must be approved public/open status.
- license_status must be open/public-compatible.
- robots_policy must allow API ingestion.
- trust_tier must be tier1 or tier2.
- governance_status must be approved.
- shadow_approved must be true.

Synthetic/test/sandbox class sources retain existing behavior for practice/test validation and are not forced through live-source governance checks.

## Real Public Sources Used by Rehearsal
- SRC-WPG-OPEN-DATA: City of Winnipeg Open Data
- SRC-CANADA-OPEN-DATA: Government of Canada Open Data

Observed persisted governance metadata from rehearsal evidence:

1. `SRC-WPG-OPEN-DATA`
- permission_status: `public`
- license_status: `government_open_data`
- rights_statement_url: `https://data.winnipeg.ca/stories/s/Open-Data-Winnipeg-Terms-of-Use/4h5q-kw4n/`
- trust_tier: `tier2`
- provenance_method: `official_api`
- governance_status: `approved`
- shadow_approved: `true`

2. `SRC-CANADA-OPEN-DATA`
- permission_status: `public`
- license_status: `government_open_data`
- rights_statement_url: `https://open.canada.ca/en/open-government-licence-canada`
- trust_tier: `tier2`
- provenance_method: `official_api`
- governance_status: `approved`
- shadow_approved: `true`

## Rights Verification Notes
- Open Government Licence - Canada explicitly allows copy/modify/distribute/use, including commercial use, with attribution requirements.
- Winnipeg terms URL used by the system is currently accessible but may redirect to sign-in for some pages depending on portal state; this should remain classified as BUILT - NEEDS TESTING for independent legal verification snapshots.

## Source Rights Evidence (Latest Rehearsal Run)

1. City of Winnipeg Open Data (`SRC-WPG-OPEN-DATA`)
- publisher: City of Winnipeg
- API/data endpoint: `https://data.winnipeg.ca/api/views.json`
- access method: HTTPS GET via official open-data API
- license/terms endpoint: `https://data.winnipeg.ca/stories/s/Open-Data-Winnipeg-Terms-of-Use/4h5q-kw4n/`
- automated access status: ALLOW
- commercial-use status: REVIEW_REQUIRED
- retrieval date: 2026-10-08
- registry classification: REVIEW_REQUIRED

2. Government of Canada Open Data (`SRC-CANADA-OPEN-DATA`)
- publisher: Government of Canada
- API/data endpoint: `https://open.canada.ca/data/en/api/3/action/package_search`
- access method: HTTPS GET via official CKAN API
- license/terms endpoint: `https://open.canada.ca/en/open-government-licence-canada`
- automated access status: ALLOW
- commercial-use status: ALLOW_WITH_ATTRIBUTION
- retrieval date: 2026-10-08
- registry classification: APPROVED

Rule applied: when rights/commercial status cannot be independently proven from currently reachable terms text, classify as REVIEW_REQUIRED and do not silently promote.

## Notes
- No REALTOR.ca scraping is used in this implementation.
- Rehearsal endpoint uses read-only public API pulls and stores provenance/citation metadata.
