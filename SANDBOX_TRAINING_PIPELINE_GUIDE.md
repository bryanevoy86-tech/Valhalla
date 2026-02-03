# SANDBOX TRAINING PIPELINE GUIDE

## Overview

This SANDBOX-safe public training data pipeline enables Valhalla's wholesaling engine to learn from open data sources without real-world execution risk. The pipeline implements hard safety gates that refuse to run outside SANDBOX environment.

✅ **SANDBOX-only** (hard safety gate via `APP_ENV` check)  
✅ **No scraping** (only open-data / ToS-safe sources)  
✅ **Copy/paste runnable**  
✅ **Extensible** (QC/BC/Atlantic/MB via config)

## Data Sources (Phase 1)

- **Edmonton Property Assessment** - Open data via Socrata API
- **Calgary Property Assessments** (current + historical) - Open data via Socrata API
- **StatsCan New Housing Price Index** - Official macro context (manual download option)

## Directory Structure

```
data/
  public_sources/
    sources.yml              # Config file listing all sources
    raw/                     # Downloaded CSV files go here

services/api/
  tools/
    public_training/
      __init__.py
      download_sources.py         # Step 1: Fetch public datasets
      import_public_data.py        # Step 2: Load into training tables
      generate_synthetic_outcomes.py  # Step 3: Generate conservative labels
      replay_wholesaling.py        # Step 4: Test against your engine (adapter TBD)
  
  public_training/
    __init__.py
    schema.py                # PublicPropertyRecord unified schema

tests/
  golden/
    wholesaling_cases.json   # Golden test cases
  test_golden_wholesaling.py # Golden test runner (pytest)
```

## What You Get

Immediately in SANDBOX:

1. **Download** public datasets (Edmonton + Calgary property assessments)
2. **Normalize** into unified schema
3. **Import** into separate training tables (never touches production leads)
4. **Generate synthetic labels** (honest + conservative outcome estimates)
5. **Replay** your wholesaling engine against synthetic data
6. **Metrics report** (accuracy, precision, recall, pursue/review rates)
7. **Golden tests** to prevent regressions

## Required Environment Variables

```bash
export APP_ENV=sandbox          # MANDATORY - refuses to run if not sandbox/dev
export DATABASE_URL="YOUR_RENDER_POSTGRES_URL"
export REPLAY_LIMIT=2000        # Optional, defaults to 1000
```

## Step-by-Step Execution

### Step 1: Download Public Sources

```bash
cd /c/dev  # or wherever your repo is
export APP_ENV=sandbox
export DATABASE_URL="postgres://..."

python services/api/tools/public_training/download_sources.py
```

**Expected output:**
```
[download_sources] Fetching edmonton_property_assessment_current (socrata_csv) -> data/public_sources/raw/edmonton_assessment_current.csv
[download_sources] Fetching calgary_property_assessment_current (socrata_csv) -> data/public_sources/raw/calgary_assessment_current.csv
[download_sources] Fetching calgary_property_assessment_historical (socrata_csv) -> data/public_sources/raw/calgary_assessment_historical.csv
[download_sources] NOTE: StatCan table is easiest to download manually:
  - Open the page
  - Choose 'CSV Download entire table'
  - Save as: data/public_sources/raw/statcan_nhpi_monthly.csv
[download_sources] Done. Successful downloads: 3/4
```

**For StatsCan:** If you want to automate, replace the StatsCan URL in `sources.yml` with a direct CSV download link from their table.

### Step 2: Import into Training Tables

```bash
python services/api/tools/public_training/import_public_data.py
```

**Expected output:**
```
[import_public_data] Loading Edmonton: data/public_sources/raw/edmonton_assessment_current.csv
[import_public_data] Loading Calgary (current): data/public_sources/raw/calgary_assessment_current.csv
[import_public_data] Loading Calgary (historical): data/public_sources/raw/calgary_assessment_historical.csv
[import_public_data] Done.
```

Creates two training-only tables in your DB:
- `public_training_properties` - Raw property records with unified schema
- `public_training_labels` - Synthetic outcome labels

### Step 3: Generate Synthetic Labels

```bash
python services/api/tools/public_training/generate_synthetic_outcomes.py
```

**Expected output:**
```
[generate_synthetic_outcomes] Labeled 45237 records (synthetic).
```

Generates conservative labels based on assessed value:
- **Below $120k**: High risk, do not pursue, confidence 0.25
- **$120k–$250k**: Medium risk, requires review, confidence 0.40
- **$250k+**: Low risk, pursue + review, confidence 0.55

### Step 4: Replay Against Your Engine

First, **wire the adapter** (one-time setup):

1. Provide the path to your wholesaling entrypoint file
2. Provide the function name that scores/offers leads

For now, you can run with the safe fallback (never pursues):

```bash
export REPLAY_LIMIT=2000
python services/api/tools/public_training/replay_wholesaling.py
```

**Expected output:**
```
=== SANDBOX REPLAY REPORT (WHOLESALING) ===
Records replayed: 2000
Pursue rate: 0.00%
Review rate: 100.00%
Accuracy (where labeled): 100.00%
Precision: 0.00%
Recall: 0.00%
TP/FP/TN/FN: 0/0/2000/0
==========================================

Next tuning levers:
- If pursue rate is too high: tighten thresholds / default review
- If FP is high: increase rejection, add risk gates, cap offers
- If FN is high: allow more borderline cases to 'review' not 'skip'
```

### Step 5: Run Golden Tests

```bash
cd /c/dev
pytest tests/test_golden_wholesaling.py -v
```

**Expected output:**
```
test_golden_wholesaling.py::test_golden_cases PASSED
```

## Safety Gates

### Hard APP_ENV Check
All tools check `APP_ENV` before running. If not in `("sandbox", "dev")`, they exit immediately:

```python
app_env = os.getenv("APP_ENV", "dev").lower()
if app_env not in ("sandbox", "dev"):
    die(f"Refusing to run in APP_ENV={app_env}. Set APP_ENV=sandbox.")
```

### Training-Only Tables
All data lives in separate `public_training_*` tables. Production lead tables are never touched.

### Conservative Label Generation
Labels intentionally reject most deals by default. Tune via constants in `generate_synthetic_outcomes.py`:
- `MAX_OFFER_TO_ASSESSMENT = 0.78` (cap at 78% of assessed value)
- `MIN_OFFER_TO_ASSESSMENT = 0.60` (low offer floor)
- `HIGH_RISK_ASSESSMENT_CEILING = 120000` (volatility threshold)

### Fallback Adapter
The replay harness defaults to "never pursue" until you wire real pipeline code.

## Future Extensibility

### Adding Province Modules

To add QC / BC / Atlantic / MB:

1. Add new data sources to `data/public_sources/sources.yml`:
   ```yaml
   - name: quebec_property_assessment
     kind: socrata_csv
     url: "https://..."
     out: "data/public_sources/raw/quebec_assessment.csv"
   ```

2. Add loader function in `import_public_data.py`:
   ```python
   def load_quebec(conn, path: str):
       # Similar pattern to load_edmonton() / load_calgary()
   ```

3. Call it in `main()`:
   ```python
   quebec_path = os.path.join(RAW_DIR, "quebec_assessment.csv")
   if os.path.exists(quebec_path):
       load_quebec(conn, quebec_path)
   ```

### Manitoba LIVE Geofence (later)

When production-ready, add these Render env vars:

```
EXECUTION_ALLOWED_PROVINCES=MB
EXECUTION_ALLOWED_CITIES=Winnipeg  # optional
TRAINING_MODE=true  # for SANDBOX
```

Then check in your LIVE action code:
```python
if not can_execute_in_province(lead.province):
    return {"skipped": "province not in EXECUTION_ALLOWED_PROVINCES"}
```

## Next Steps

**When you're back at VS Code:**

1. Paste the path to your wholesaling entrypoint file (e.g., `services/api/app/services/lead_scoring.py`)
2. Paste the function name (e.g., `score_lead` or `evaluate_wholesaling_opportunity`)
3. I'll write the exact adapter import so replay uses your real pipeline

**Example:**
```
Path: services/api/app/services/lead_scoring.py
Function: evaluate_lead(lead_dict) -> {"should_pursue": bool, "offer_low": float, "offer_high": float, "human_review_required": bool}
```

Then replay will test your actual logic against 1000+ public records and generate real metrics.

## Troubleshooting

### "APP_ENV not set" Error

Make sure to export it before running:
```bash
export APP_ENV=sandbox
python services/api/tools/public_training/download_sources.py
```

### "DATABASE_URL not set" Error

Your DATABASE_URL must be in environment:
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

### StatsCan Download Failed

The script treats StatsCan as manual because their table page is HTML. To automate:
1. Go to https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810020501
2. Click "Download entire table as CSV"
3. Note the direct CSV URL
4. Replace in `sources.yml` with that direct URL

### Train Tables Already Exist

Scripts use `ON CONFLICT ... DO UPDATE`, so re-running is safe. Old labels are overwritten.

## Files Reference

| File | Purpose | Safe to Edit |
|------|---------|-------------|
| `data/public_sources/sources.yml` | Data source URLs + paths | ✅ Add sources here |
| `download_sources.py` | Fetches CSVs from URLs | ⚠️ Only if adding new source kinds |
| `schema.py` | PublicPropertyRecord dataclass | ✅ Add fields as needed |
| `import_public_data.py` | CSV → DB loader | ✅ Add loaders for new provinces |
| `generate_synthetic_outcomes.py` | Outcome label generation | ✅ Tune constants (MAX_OFFER, etc.) |
| `replay_wholesaling.py` | Adapter + metrics | ⚠️ Only change adapter placeholder |
| `wholesaling_cases.json` | Golden test data | ✅ Add test cases |
| `test_golden_wholesaling.py` | Test runner | ⚠️ Usually stable |

---

**All SANDBOX. Hard gates. Copy/paste ready. Extensible. Test early.**
