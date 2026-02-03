# QUICK START: SANDBOX TRAINING PIPELINE

## One-Time Setup

### Windows PowerShell
```powershell
cd C:\dev\valhalla
$env:APP_ENV="sandbox"
$env:DATABASE_URL="postgresql://..."  # Your Render DB URL
```

### Windows Command Prompt (cmd.exe)
```cmd
cd C:\dev\valhalla
set APP_ENV=sandbox
set DATABASE_URL=postgresql://...
```

### macOS / Linux
```bash
cd ~/path/to/valhalla
export APP_ENV=sandbox
export DATABASE_URL="postgresql://..."
```

## Execute the Full Pipeline (5 Steps)

### Step 1: Download Public Data
```bash
python services/api/tools/public_training/download_sources.py
```
✅ Fetches Edmonton, Calgary property assessments + StatsCan NHPI

### Step 2: Import into Training Tables
```bash
python services/api/tools/public_training/import_public_data.py
```
✅ Creates `public_training_properties` and `public_training_labels` tables

### Step 3: Generate Synthetic Labels
```bash
python services/api/tools/public_training/generate_synthetic_outcomes.py
```
✅ Labels ~45k+ records (conservative: mostly reject, flag for review)

### Step 4: Replay Against Your Engine
```bash
# PowerShell
$env:REPLAY_LIMIT="2000"
python services/api/tools/public_training/replay_wholesaling.py

# OR Command Prompt
set REPLAY_LIMIT=2000
python services/api/tools/public_training/replay_wholesaling.py
```
✅ Tests wholesaling logic, generates metrics (accuracy, precision, recall)

### Step 5: Run Golden Tests
```bash
pytest tests/test_golden_wholesaling.py -v
```
✅ Regression protection (fails if behavior changes unexpectedly)

## Output Explained

**After Step 3 (synthetic labels):**
```
[generate_synthetic_outcomes] Labeled 45237 records (synthetic).
```

**After Step 4 (replay metrics):**
```
=== SANDBOX REPLAY REPORT (WHOLESALING) ===
Records replayed: 2000
Pursue rate: 0.00%          ← Percentage of deals pursued
Review rate: 100.00%        ← Percentage flagged for human review
Accuracy: 100.00%           ← Classification accuracy
Precision: 0.00%            ← True positives / (true + false positives)
Recall: 0.00%               ← True positives / (true positives + false negatives)
TP/FP/TN/FN: 0/0/2000/0    ← Confusion matrix
```

## Safety Gates

✅ **Hard APP_ENV Check** - Refuses to run unless `APP_ENV=sandbox` or `dev`  
✅ **Training-Only Tables** - Never touches production lead tables  
✅ **Conservative Labels** - Defaults to reject/review (safe by default)  
✅ **Fallback Adapter** - Never pursues unless you wire real logic

## Next Step (Wire Your Wholesaling Logic)

Once you're ready, provide:
1. **Path to wholesaling entrypoint file** (e.g., `services/api/app/services/lead_scoring.py`)
2. **Function name** (e.g., `evaluate_lead`)
3. **Expected return format**:
   ```python
   {
       "should_pursue": bool,
       "offer_low": float | None,
       "offer_high": float | None,
       "human_review_required": bool
   }
   ```

Then I'll wire the adapter so replay uses your actual engine.

## Verify Setup Works

### 1. Check Database Tables Populated

Run in your PostgreSQL client:
```sql
SELECT COUNT(*) as property_count FROM public_training_properties;
SELECT COUNT(*) as label_count FROM public_training_labels;
```

**Expected**: Both > 0 (if 0, check download_sources.py output for failed URLs)

### 2. Verify Golden Tests Pass

```bash
pytest tests/test_golden_wholesaling.py -v
```

**Expected**: ✅ test_golden_cases PASSED

### 3. Check Replay Output

Last 5 lines should show metrics like:
```
Records replayed: 2000
Pursue rate: 0.XX%
Review rate: 0.XX%
Accuracy: 0.XX%
```

## Files Created

| File | Purpose |
|------|---------|
| `data/public_sources/sources.yml` | Data source URLs + output paths |
| `data/public_sources/raw/` | Downloaded CSV files |
| `services/api/tools/public_training/download_sources.py` | Step 1 - Fetch data |
| `services/api/tools/public_training/import_public_data.py` | Step 2 - Load to DB |
| `services/api/tools/public_training/generate_synthetic_outcomes.py` | Step 3 - Generate labels |
| `services/api/tools/public_training/replay_wholesaling.py` | Step 4 - Test + metrics |
| `tests/golden/wholesaling_cases.json` | Test cases |
| `tests/test_golden_wholesaling.py` | Step 5 - Golden test runner |
| `SANDBOX_TRAINING_PIPELINE_GUIDE.md` | Full documentation |

## Tuning Constants (Edit as Needed)

In `generate_synthetic_outcomes.py`:
```python
MAX_OFFER_TO_ASSESSMENT = 0.78      # Cap offer at 78% of assessed value
MIN_OFFER_TO_ASSESSMENT = 0.60      # Floor at 60%
HIGH_RISK_ASSESSMENT_CEILING = 120000  # Below this = high risk
```

## Extending to New Provinces

1. Add source URL to `data/public_sources/sources.yml`
2. Create loader function in `import_public_data.py` (copy `load_calgary` pattern)
3. Call it from `main()`
4. Done!

## Manitoba LIVE Geofence (Future)

When production-ready, add Render env vars:
```
EXECUTION_ALLOWED_PROVINCES=MB
TRAINING_MODE=true
```

Then check in your LIVE execution code before taking real-world actions.

---

**SANDBOX Only. Hard Gates. Copy/Paste Ready.**
