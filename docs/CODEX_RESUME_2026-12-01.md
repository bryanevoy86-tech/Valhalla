# Codex / VS Code — Valhalla Resume Handoff

Planned resumption: when local Codex usage allowance refreshes, expected December 1, 2026.

DO NOT restart the project, regenerate completed packs, or treat API presence as operating business evidence.

## Repository and change control

- GitHub: https://github.com/bryanevoy86-tech/Valhalla
- Stable Render production branch: main (auto-deploy on push).
- Working development branch: fix/fail-closed-operations-20261119
- Draft PR: https://github.com/bryanevoy86-tech/Valhalla/pull/4
- Persistent changelog: ops/CHANGE_LEDGER.md
- Definition of done: docs/HEIMDALL_DEFINITION_OF_DONE.md
- Existing architecture: docs/PHASE3_INTEGRATED_ARCHITECTURE.md and docs/UNIVERSAL_OPPORTUNITY_PIPELINE.md

### Safely retrieve current work

From your existing local folder C:\dev\valhalla:

    git status --short
    git fetch origin
    git switch -c codex-business-factory origin/fix/fail-closed-operations-20261119

If there are uncommitted local changes, preserve them before switching. Do NOT reset or delete local work. If the branch name exists already, choose a new name. Codex must compare local-only work against GitHub before merging any changes.

## Code already on the development branch

- Scheduler, reference outbox dispatcher, daily ops and cron runner corrected to stop reporting nonexistent successes.
- Heimdall readiness changed to conservative evidence-based checks.
- New Business Factory worker in services/api/app/services/prime_business_execution.py.
- New authenticated endpoints in services/api/app/routers/prime_business_factory.py.
- Existing DB records reused: LegacyInstanceWorkItem, LegacyOrchestrationEvent, LegacyInstanceRegistryItem and MediaContent.
- Five false-success smoke tests plus five SQLAlchemy/FastAPI integrated Business Factory lifecycle tests.
- CI workflow: .github/workflows/critical-controls-ci.yml.
- Initial false-success CI: https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44630305972
- Business Factory integration CI: https://github.com/bryanevoy86-tech/Valhalla/actions/runs/44635299115

New pilot is INTERNAL_DRAFT_ONLY: persistent, idempotent, owner-approved, verified record and receipt. No claim of a storefront, payments, generated downloads, marketing or sale. All new pilot API calls require X-Business-Factory-Key, compared to the secure server-side VALHALLA_FACTORY_KEY. Missing key = HTTP 503. The required key has NOT been set on Render in this work.

## Required Codex next actions (in order)

1. Read the ledger, acceptance contract, this handoff and PR #4 before writing code.
2. Fetch the branch. Run focused and integrated CI tests in an isolated environment. Review tests for meaningful proof and inspect legacy full-suite errors without hiding or ignoring them.
3. Inspect the current factory service and route for full import/auto-registration, database concurrency safety, idempotency collision protection, governance, safe auth, policy sync, status reporting, receipt integrity, and actual behavior.
4. Verify which Postgres database production API uses, without exposing credentials or changing schemas. Current Render inspection showed one empty public schema and one with 367 tables.
5. Implement and prove a durable worker scheduler with safe retries and restart behavior on actual Postgres, using the existing work registry. Do not use in-memory state for business-critical jobs.
6. Build the minimum actual Product Foundry loop in this same execution system: validate asset bytes/hash/version and license; owner-approved storefront listing; payment-provider verified sale; delivered download; refund/reconciliation; accurate daily profit summary.
7. Connect actual authorized marketing, campaign attribution, and conversion reporting. No false "published" status, spamming, or paid advertising without approval.
8. Feed actual outcomes to Mimir and reuse existing cross-industry opportunity scoring. Then add source-driven independent discovery that produces the same governed work records.
9. Re-run complete tests. Maintain an evidence table per capability: code, focused test, real integrated test, staging proof, deployed commit, live receipt and outcome.
10. Propose a controlled deployment and rollback plan for owner approval. Do not push to main or change Render service configuration without that approval.

## Current Render inspection — 2026-11-19

- Workspace: tea-d3fbf3r3fgac73b3ed40
- API service srv-d3hatinfte5s73cqbbh0: live Git commit 93cb1afe (October 10).
- Daily email cron crn-d5u469npm1nc73d9n350: recent successful runs, not a business task executor.
- Postgres dpg-d90l1mv7f7vs73cod580-a: public tables = 0.
- Postgres dpg-d9ek3oj7uimc73fooes0-a: public tables = 367.
- No Render production changes have been made by this effort.
- Production API database identity remains unverified.
- Do not print or commit credentials. Do not create new paid Render services casually.

## Paste this prompt into Codex on resumption

Continue the CURRENT Valhalla / Heimdall Prime codebase. Start with a safe git fetch, review GitHub PR #4 (branch fix/fail-closed-operations-20261119), and read ops/CHANGE_LEDGER.md, docs/CODEX_RESUME_2026-12-01.md, docs/HEIMDALL_DEFINITION_OF_DONE.md and docs/PHASE3_INTEGRATED_ARCHITECTURE.md. Preserve all existing local-only changes. DO NOT create more standalone packs, reset the repository, or mark simulated functionality complete. Verify the real FastAPI and SQLAlchemy integration of the new owner-approved Business Factory execution lane and its SHA-256 receipts. Run all new CI checks, diagnose broad-suite failures, and then build the missing durable Postgres worker/recovery, actual product artifact storage, provider-backed storefront fulfilment, verified sales/refunds/accounting, lawful automated marketing, and proactive multi-industry opportunity discovery into ONE canonical governed end-to-end lifecycle. Reuse the existing Prime, legacy, Phase Three evaluator and Mimir modules wherever possible. Record every file/commit, CI link, Render action and real-world evidence in ops/CHANGE_LEDGER.md. Do not push to main or deploy production until I authorize a reviewed release; do not expose secrets or spend funds. The final deliverable must demonstrate a real business from independent discovery through verified execution, customer delivery, and reconciled profit, not endpoints that only return success.

## Handoff success criteria

- Local Codex reads exact committed GitHub changes, not reconstructed chat prompts.
- Tests pass in a clean checkout, with known failures recorded.
- Every operation returning completed has an independently verifiable receipt.
- Any remaining setup requiring the owner's external accounts or legal/financial approvals is explicitly identified.
- No production impact until a reviewed release is authorized.


## Added after initial handoff: scheduled execution and database preparation (Nov 19)

- Existing Render daily cron command is services/api/tools/cron/daily_email_ping.py. It now optionally calls business_factory_tick.py AFTER successful email; no second paid cron service is created.
- The optional tick is DISABLED by default. It requires BOTH BUSINESS_FACTORY_RUN_URL and VALHALLA_FACTORY_KEY. The URL must be HTTPS, an exact path, and an explicitly allowed host. It rejects redirects, missing credentials and unverifiable success.
- No keys or URLs were configured on live Render. This is SOURCE-CODE PREPARATION, not a deployed worker.
- The populated Render Postgres db-v2-copy was inspected read-only. It has media_contents and alembic_version, but is missing legacy_instance_registry_items, legacy_instance_work_items and legacy_orchestration_events.
- Its current alembic_version was 8e43f380be7f on Nov 19. The repository has an existing subsequent revision 20261007_shadow_source_governance.
- Migration alembic/versions/20261119_factory_legacy_work_schema.py now prepares missing factory tables after the existing governance revision. It preserves existing tables and will not drop business data on downgrade. Review and apply only on an approved deployment.
- API router requires all four persistent tables before running. It returns HTTP 503 with missing-table details rather than reporting false success.
- More tests: tests/test_business_factory_cron.py and tests/test_factory_migration.py. The GitHub workflow exercises dry-run email/worker-cron security and idempotent non-destructive migration against disposable SQLite.
- Root alembic is at alembic/ (not services/api/alembic/). Dockerfile starts services/api/start.py. Render web service currently has an empty pre-deploy command. Do not assume migrations happen automatically.
- Before any production deployment: establish which database the API actually uses, run an isolated migration rehearsal, validate new auth, review live business data and rollback posture, then obtain owner approval.

**Current live Render services and database have NOT been mutated.** Updating GitHub's isolated development branch does not change Render production until main changes or a deployment is explicitly triggered.
