# First operating loop evidence

November 24, 2026. Disposable services and synthetic records only. This extends the [operational audit](VALHALLA_AUTONOMY_OPERATIONAL_AUDIT.md) without changing any acceptance contract. The worker closes the bounded one-time CAD chain from an already reviewed decision and final mandate. A complete hands-off run from source intake through Prime selection remains open.

## Actor ledger

| Transition | Actual actor and evidence |
|---|---|
| Pre-run source and scope | Test harness provisions disposable scope, buyer, product, campaign and economic records. It submits signed source and synthetic research and invokes existing source and Pantheon operations. It is input/setup, with some owner-gated calls. |
| Independent review | Existing Loki analyst tick connects to the loopback queue with only the reviewer key, runs analysis, and posts results for the exact opportunity and Pantheon report. Material findings hold the decision. The test harness acts under the fixture owner key to resolve them before the final mandate. |
| Initial Prime decision | Harness calls existing Phase 3 evaluation with the cleared proposal. Prime writes the scoped verdict and a separate test reads the bound decision. This is a direct test call, outside worker dispatch. |
| Final mandate | One owner-authenticated request binds the verified verdict, artifact, campaign, verified disposable buyer, terms digest, exact CAD offer, expiry and fixture cost. It grants one internal listing draft. |
| Listing and sale dispatch | An actual worker process polls the loopback API with only Prime authority. It validates the mandate and current review, queues and executes the Factory listing, then creates the consent-bound attribution and order after buyer input. |
| Voluntary enrollment and purchase | Harness acting as a buyer uses only their signed-in bearer session and accepts the terms. No Prime or owner credential is supplied by that actor. |
| Payment and delivery | Harness acting as a separate payment fixture sends a scoped signed capture. The worker waits until it arrives, records delivery, and the buyer downloads and acknowledges the exact artifact. The fixture payment adapter cannot call a provider. |
| Support and refund | The buyer requests support. Worker records one full-refund intent. The harness supplies the provider's separately signed refund callback. Access is denied afterwards. The worker then closes the case from reconciled evidence. |
| Statement, obligations and Mimir | Harness acting as a separate bank fixture signs an exact statement. Worker matches both transfers, records cost and support receipts, stores settlement-backed performance and verifies the Mimir outcome. Closed cash and obligations are zero. No revenue ledger entry is written. |
| Recovery and replay | Test harness starts short-lived CLI worker processes, shuts down and restarts the loopback server, and reopens the file database. It injects a stop, changes a Loki result reference, interrupts the accounting transaction after the settlement flushes, and changes a stored settlement to test denial. It restores controlled faults where required. These are harness actions and confer no operating authority. |

Every successful transition from the final mandate has a unique idempotent identifier, scope, actor and chained SHA-256 receipt. Same-input payment and buyer replays return the prior receipts. Worker replay rechecks Mimir against the native settlement and fails if the evidence diverges. No new external payment, bank movement, product publication, outreach, or live delivery can occur from this rehearsal.

## Reproduce

In an isolated checkout with the test environment installed, run:

```bash
DATABASE_URL=sqlite:// VALHALLA_JWT_SECRET=local-isolated-fixture \
VALHALLA_OWNER_USERNAME=fixture-owner VALHALLA_OWNER_PASSWORD=internal-fixture-only \
ENV=dev APP_ENV=dev VALHALLA_EMERGENCY_STOP=true \
python -m pytest -o addopts='' -qs services/api/tests/test_product_artifact_workflow.py -k operating-loop
```

The case emits a redacted `FOUNDRY_OPERATING_REHEARSAL` receipt chain. Identities, specimen terms and provider signing secrets are disposable. The new routes are off by default and reject staging/live mode. For a disposable run only, enable `VALHALLA_FOUNDRY_OPERATING_REHEARSAL=1`. The API keeps `VALHALLA_FOUNDRY_FIXTURE_SECRET` and `VALHALLA_OPERATING_FIXTURE_BANK_SECRET` separate from the distinct Prime, owner, buyer and Loki identities. The worker receives only the Prime control key and connects to the disposable API over loopback. It polls by run UUID. Never expose the fixture inputs on a hosted Preview or with real identities.

## Remaining breaks and commissioning sequence

1. Connect authorized discovery/report cadence to exact candidate preparation and Prime evaluation. Automatically queue and consume independent challenge receipts. Preserve an explicit hold for unresolved material findings and keep final authority with the owner. This run used pre-mandate owner dispositions and a harness-invoked Prime evaluation, so it does not prove that upstream loop.
2. The worker records a refund intent. The test payment actor supplies the callback manually. Connect an approved processor sandbox action and its independent callback/readback before claiming routine provider-side refund operation. The statement actor is similarly simulated. Commission bank or accountant-controlled readback and exact statement matching separately.
3. The [costed staging options and approvals](VALHALLA_STAGING_PROVISIONING.md#cost-comparison-in-usd) remain the controlling external plan. Hold procurement until the internal source-to-outcome proof passes. Commission only isolated WeWeb Preview and exact CORS, distinct Render API/worker/reviewer/database/restore identities, restricted Stripe sandbox, independently reviewed accounting and one permission-based acquisition channel. Use actual provider quotes and explicit authority before spending, publishing, collecting live evidence or running the elapsed trial. No full-lifecycle commercial acceptance is claimed.
