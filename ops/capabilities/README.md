# Valhalla Dormant Capabilities

Goal: keep tools dormant until the right moment.

## Rules

- Auto-surface only CERTIFIED items
- Auto-run never
- Anything irreversible is always human-gated
- Keep suggestions to 1–3 items max to avoid noise

## Use

**Suggest:** Get relevant capabilities based on context
```
python ops/scripts/capability_suggest.py "context text"
```

**Explain run:** See how to run a specific capability
```
python ops/scripts/capability_run.py <capability_id>
```

## Test Now (Safe)

These don't touch the running sandbox:

```bash
python ops/scripts/capability_suggest.py "I opened a new bank account at RBC for operating CAD"
python ops/scripts/capability_suggest.py "I need to send paperwork to EIA"
python ops/scripts/capability_suggest.py "There are too many export files and storage is filling up"
python ops/scripts/capability_run.py banking_intake_wizard
```

## Status

**CERTIFIED (Auto-surfaced):**
- Banking Intake Wizard
- Handoff Pack Generator
- Export Cleanup & Retention
- Repo Smoke Check

**DORMANT (Inert, activate later):**
- GO Preflight
- Buyer Pipeline Starter
- Third-Party Payee Workflow
