# GO-Time Preflight (Valhalla)

## Non-Negotiables
- No runtime contamination during certification.
- No outbound enabled without explicit GO decision.
- No capabilities may auto-run.

---

## 1) Sandbox / Runtime Safety
- [ ] DRY_RUN = 0 is NOT enabled yet (should still be DRY_RUN=1 until GO)
- [ ] OUTBOUND_DISABLED = 1 (until GO)
- [ ] DB isolation verified (sandbox/isolated DB)
- [ ] No new imports added to hot path during certification window

---

## 2) Capability Governance
- [ ] Registry lints clean: `python ops/scripts/lint_registry.py`
- [ ] Cold-zone check passes: `python ops/scripts/coldzone_check.py`
- [ ] Certified-only suggestion works: `python ops/scripts/suggest_certified.py "lawyer deal packet"`
- [ ] Any capability that is GATED remains GATED unless explicitly approved

---

## 3) Freeze for GO
- [ ] Freeze ON: `python ops/scripts/freeze_capabilities.py on --by "Bryan" --reason "GO lock"`
- [ ] Audit entry written: `python ops/scripts/audit_append.py --actor "Bryan" --action "freeze" --details "GO lock enabled"`

---

## 4) Data & Outputs
- [ ] Output folder exists: `ops/handoff/output/`
- [ ] No secrets in generated packs (spot check)

---

## 5) Final Decision Gate
- [ ] GO decision made explicitly (date/time noted)
- [ ] Outbound enabling plan documented
- [ ] Kill switch verified reachable
