# Valhalla Pack Tracker Guide

## Quick Start

The tracker scans your codebase for PACK declarations and tracks implementation status.

### 1. Update the Manifest
Scan all code and rebuild the manifest:
```bash
cd c:\dev\valhalla
python valhalla_pack_tracker.py update
```

**Output**: Updates `valhalla_manifest.json` with discovered packs and units

### 2. Generate Snapshot (for ChatGPT)
Create a comprehensive snapshot of what's built:
```bash
python valhalla_pack_tracker.py summary > pack_snapshot.txt
```

**Output**: Formatted report showing:
- **PACKS — COMPLETE**: Fully implemented (router + service + model/schema)
- **PACKS — PARTIAL**: Some components exist but incomplete
- **PACKS — PLANNED ONLY**: No code yet or no components
- **UNITS — COMPLETE**: Code units with all 4 components (model, schema, service, router)
- **UNITS — PARTIAL**: Code units with some components
- **UNITS — PLANNED**: Code units with no components
- **Full details** of each PACK and UNIT with file locations

## What It Tracks

### PACKs
Recognized by `PACK [ID]` headers in your code:
```python
# PACK CL9 — Decision Outcome Log & Feedback API
# PACK CI5 — Tuning Ruleset Engine
```

**Status Levels**:
- **complete**: Has router + service + (model OR schema)
- **partial**: Some components exist but not enough for complete
- **planned**: No code components at all

### UNITs
File-based code features based on filename (stem):
- `decision_outcome.py` → unit `decision_outcome`
- `tuning_rules.py` → unit `tuning_rules`

**Components**:
- **model**: ORM model file (models/*.py)
- **schema**: Pydantic schema (schemas/*.py)
- **service**: Business logic (services/*.py)
- **router**: FastAPI endpoints (routers/*.py)
- **migration**: Alembic migration (alembic/versions/*.py)
- **other**: Everything else

**Status Levels** (same as PACKs):
- **complete**: Has all 4 core components (model, schema, service, router)
- **partial**: Has some components
- **planned**: No components

## Manifest Structure

`valhalla_manifest.json` contains:

```json
{
  "generated_at": "2025-12-07T...",
  "planned_packs": { },
  "packs": {
    "CL9": {
      "title": "Decision Outcome Log & Feedback API",
      "status": "partial",
      "components": { "router": true, "service": true, ... },
      "files": [
        { "file": "services/api/app/routers/...", "line": N, "preview": "..." }
      ]
    }
  },
  "units": {
    "decision_outcome": {
      "status": "complete",
      "components": { "model": true, "schema": true, ... },
      "packs": ["CL9"],
      "files": [...]
    }
  }
}
```

## Search Directories

The tracker scans these folders for Python files:
- `app/`
- `backend/`
- `services/api/app/`

To add more, edit `SEARCH_DIRS` in `valhalla_pack_tracker.py`

## Use Cases

### 1. Check Implementation Status
```bash
python valhalla_pack_tracker.py summary
```
Quickly see which PACKs are complete, partial, or planned.

### 2. Find Units by Component
Search the manifest JSON:
```bash
# Find all complete units
cat pack_snapshot.txt | grep "UNITS — COMPLETE" -A 100
```

### 3. Track New PACK Implementation
1. Add a `PACK [ID]` header to your files:
   ```python
   # PACK CI9 — Some New Feature
   ```
2. Create models, schemas, services, routers
3. Run `python valhalla_pack_tracker.py update`
4. Check status with `python valhalla_pack_tracker.py summary`

### 4. Identify Incomplete Work
```bash
python valhalla_pack_tracker.py summary | grep "PARTIAL"
```
Shows PACKs and UNITs that need more components.

## Example Workflow

```bash
# 1. Start a new PACK
# Add to services/api/app/models/my_feature.py:
# PACK SX1 — My New Feature

# 2. Update manifest
python valhalla_pack_tracker.py update

# 3. Check status
python valhalla_pack_tracker.py summary

# Output: SX1 is "partial" (has model, needs schema/service/router)

# 4. Add more components
# - services/api/app/schemas/my_feature.py
# - services/api/app/services/my_feature.py
# - services/api/app/routers/my_feature.py

# 5. Verify completion
python valhalla_pack_tracker.py update
python valhalla_pack_tracker.py summary

# Output: SX1 is "complete"
```

## Passing Output to ChatGPT

Save the summary and paste it:
```bash
python valhalla_pack_tracker.py summary > snapshot_for_gpt.txt
```

Share `snapshot_for_gpt.txt` to get AI analysis of your implementation status.

## Files

- **valhalla_manifest.json**: Machine-readable manifest (13.8MB with 621 units)
- **valhalla_pack_tracker.py**: Python script (13.4KB)
- **pack_snapshot.txt**: Human-readable snapshot (277KB)

## Performance Notes

- First run scans ~620 Python files (slower)
- Subsequent runs use manifest (faster)
- Call `update` only when code changes significantly
- Use `summary` to generate reports (calls `update` first)
