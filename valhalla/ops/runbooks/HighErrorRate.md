# HighErrorRate

**Summary**: Too many 5xx from Valhalla.

## Checks
1. `kubectl logs` on backend pods
2. /admin/ops-triage for offending paths
3. Rollback canary if active

## Remediation
- Revert latest deploy
- Clear hot cache if error is cache-related
