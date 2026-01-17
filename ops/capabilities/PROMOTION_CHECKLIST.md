# Capability Promotion Checklist (DORMANT → CERTIFIED → LIVE)

## Definitions
- DORMANT: Exists, referenced in registry, does nothing unless manually invoked.
- CERTIFIED: Manually verified safe. Heimdall may auto-surface (suggest), but never execute.
- LIVE: Allowed to run actions (rare; requires explicit operator approval gates).

---

## DORMANT → CERTIFIED (Required)
1) File existence
- All referenced files exist (md/scripts).
- All paths in registry match real paths.

2) Safety guarantees
- No outbound network calls.
- No credential access.
- No writing to runtime config or production DB.
- Output limited to ops/handoff/output (or another explicit safe output folder).

3) Local-only behavior
- Reads only local files and user-provided inputs.
- Creates folders/files only in safe output paths.

4) Dry-run discipline
- If the script has a "run" behavior, it must support dry-run OR produce only documents/templates.

5) Minimal test run (must pass)
- Capability suggest returns it when triggered.
- Runner prints instructions only (or runs locally but only outputs to safe folder).
- Script executes successfully with sample input.

6) Logging / trace
- Certification log entry created with:
  - who certified
  - when
  - what tests were run
  - notes

✅ If all 6 pass → CERTIFIED allowed.

---

## CERTIFIED → LIVE (Rare)
Requires:
- explicit operator approval mechanism
- caps/whitelists/idempotency
- kill switch
- audit log
- sandbox trial first

Default rule: keep most things CERTIFIED, not LIVE.
