# Data Hygiene & Retention Policy (INTERNAL)

## Principle
We do not delete core learning/audit data prematurely.
We *rotate artifacts* and *age out waste* safely.

## Categories
1) Core records (DB): retain per legal/tax requirements
2) Artifacts (exports/reports): rotate and compress
3) Quarantine: keep long enough to debug input issues, then purge
4) Temp files: delete aggressively

## Recommended Retention (safe defaults)
- Raw exports (bulk): keep 14–30 days, then compress
- Integrated sandbox reports: keep 30–90 days, then compress
- Daily digests: keep indefinitely (tiny, high value)
- Quarantine: keep 90 days, purge after (unless investigating)
- Temp scratch: purge daily/weekly

## Deletion Guardrails
- Never delete anything under investigation
- Never delete anything referenced by:
  - legal/tax documentation
  - proof packs
  - active disputes
- Prefer compression over deletion
