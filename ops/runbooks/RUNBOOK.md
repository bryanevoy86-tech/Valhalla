# Valhalla Operator Runbook (Cold-Zone)

## Golden Rule
Do not modify or restart the running sandbox process during certification.

## Daily Operator Routine (low noise)
1) Check sandbox status output (no changes)
2) Run smoke checks (optional)
3) Generate handoff packs if needed
4) Cleanup old exports (optional, safe)

## Safety
- Never commit secrets
- Never log tokens
- Never enable outbound during sandbox
