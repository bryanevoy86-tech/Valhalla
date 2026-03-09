# Verify Checklist (Fast)

## Pre-flight
- [ ] Sandbox is running (do not restart)
- [ ] No changes made to sandbox runner / guards under test

## Repo sanity
- [ ] No `.env` committed
- [ ] No tokens/secrets in files
- [ ] New scripts are NOT imported by app startup

## Optional smoke check
- [ ] python ops/scripts/smoke_check.py

## Optional cleanup (only deletes old exports)
- [ ] python ops/scripts/cleanup_exports.py --dry-run
- [ ] python ops/scripts/cleanup_exports.py --apply

## Optional handoff packs
- [ ] python ops/scripts/generate_handoff_packs.py
