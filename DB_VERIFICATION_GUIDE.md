# DATABASE VERIFICATION GUIDE

**Purpose**: Quick sanity checks after running import_public_data.py to confirm tables are populated.

---

## Quick Checks (3 Queries)

### Query 1: Count Training Properties

```sql
SELECT COUNT(*) as total_properties
FROM public_training_properties;
```

**Expected**: > 0 (typically 10k–50k+ depending on dataset size)  
**If 0**: CSV download failed or column mapping didn't match. Check download_sources.py output.

### Query 2: Count Training Labels

```sql
SELECT COUNT(*) as total_labels
FROM public_training_labels;
```

**Expected**: > 0 (should match or be close to total_properties)  
**If 0**: generate_synthetic_outcomes.py didn't run or failed silently.

### Query 3: Sanity Check Label Distribution

```sql
SELECT 
    risk_level,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percent
FROM public_training_labels
GROUP BY risk_level
ORDER BY count DESC;
```

**Expected output** (example):
```
risk_level   | count | percent
-------------|-------|--------
medium       | 18234 | 52.3%
low          | 10891 | 31.2%
high         | 5112  | 14.7%
```

**Interpretation**:
- High: Lowest value, high risk (rejected by design)
- Medium: Mid-value (mostly review)
- Low: Highest value (can pursue with review)

### Query 4: Offer Band Sanity Check

```sql
SELECT 
    COUNT(*) as labeled_records,
    ROUND(MIN(offer_low), 0) as min_offer_low,
    ROUND(MAX(offer_low), 0) as max_offer_low,
    ROUND(MIN(offer_high), 0) as min_offer_high,
    ROUND(MAX(offer_high), 0) as max_offer_high,
    ROUND(AVG(offer_high / assessed_value), 4) as avg_offer_ratio
FROM public_training_labels
WHERE offer_low IS NOT NULL AND offer_high IS NOT NULL AND assessed_value > 0;
```

**Expected**:
- `avg_offer_ratio` ≈ 0.69 (halfway between 0.60 floor and 0.78 cap)
- `offer_low` > 0 and `offer_high` > `offer_low`
- All ratios should be between 0.59 and 0.79

---

## If Something's Wrong

### Scenario 1: Both Tables Are Empty (0 rows)

**Cause**: CSV files didn't download or import didn't run  
**Fix**:
```bash
# 1. Check raw CSV files exist
ls -la data/public_sources/raw/

# 2. If missing, re-run download
python services/api/tools/public_training/download_sources.py

# 3. Check output for errors (URL timeouts, file not found, etc.)

# 4. Then re-run import
python services/api/tools/public_training/import_public_data.py
```

### Scenario 2: Properties Populated, Labels Empty

**Cause**: generate_synthetic_outcomes.py didn't run  
**Fix**:
```bash
python services/api/tools/public_training/generate_synthetic_outcomes.py
```

### Scenario 3: Properties Empty, Labels Not Empty (Weird)

**Cause**: Import ran but properties didn't insert  
**Fix**: Check CSV column names. Common issue: Edmonton uses "Account Number" but code expects different name.

**Quick fix**: Edit `load_edmonton()` in `import_public_data.py` to print actual column names:
```python
print(f"Columns: {list(r.keys())}")  # Add this inside the loop, first iteration
```

Then update column mappings in the code.

### Scenario 4: Offer Ratio > 0.78 or < 0.60

**Cause**: Label generation constants were changed or import used old data  
**Fix**:
```bash
# Option 1: Regenerate labels (will overwrite)
python services/api/tools/public_training/generate_synthetic_outcomes.py

# Option 2: Check constants in generate_synthetic_outcomes.py
# MAX_OFFER_TO_ASSESSMENT = 0.78  # Should be this
# MIN_OFFER_TO_ASSESSMENT = 0.60  # Should be this
```

---

## Full Verification Script (SQL + Python)

### Run This After Import

```bash
# Step 1: Check table existence and row counts
python -c "
from sqlalchemy import create_engine, text
import os

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('ERROR: DATABASE_URL not set')
    exit(1)

engine = create_engine(db_url, future=True)

with engine.begin() as conn:
    # Check tables exist
    result = conn.execute(text('''
        SELECT COUNT(*) FROM public_training_properties;
    '''))
    prop_count = result.scalar()
    
    result = conn.execute(text('''
        SELECT COUNT(*) FROM public_training_labels;
    '''))
    label_count = result.scalar()
    
    print(f'✅ public_training_properties: {prop_count} rows')
    print(f'✅ public_training_labels: {label_count} rows')
    
    if prop_count == 0:
        print('⚠️  WARNING: properties table is empty. Check downloads.')
    if label_count == 0:
        print('⚠️  WARNING: labels table is empty. Run generate_synthetic_outcomes.py')
"
```

### Run This in Python to Check Metrics

```python
from sqlalchemy import create_engine, text
import os

db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url, future=True)

with engine.begin() as conn:
    # Risk distribution
    result = conn.execute(text('''
        SELECT risk_level, COUNT(*) as count
        FROM public_training_labels
        GROUP BY risk_level
        ORDER BY count DESC;
    '''))
    
    print("Risk Distribution:")
    for risk, count in result:
        print(f"  {risk}: {count}")
    
    # Offer band check
    result = conn.execute(text('''
        SELECT 
            ROUND(AVG(offer_high / assessed_value), 4) as avg_ratio,
            ROUND(MIN(offer_high / assessed_value), 4) as min_ratio,
            ROUND(MAX(offer_high / assessed_value), 4) as max_ratio
        FROM public_training_labels
        WHERE assessed_value > 0;
    '''))
    
    avg_r, min_r, max_r = result.fetchone()
    print(f"\nOffer Band Ratio:")
    print(f"  Average: {avg_r} (expected ~0.69)")
    print(f"  Min: {min_r} (expected ~0.60)")
    print(f"  Max: {max_r} (expected ~0.78)")
    
    if avg_r and (avg_r < 0.55 or avg_r > 0.80):
        print("  ⚠️  WARNING: Ratio outside expected range. Check constants.")
```

---

## Success Criteria

✅ **Green Light** (All OK):
```
public_training_properties: 45237 rows
public_training_labels: 45237 rows

Risk Distribution:
  medium: 23612
  low: 14087
  high: 7538

Offer Band Ratio:
  Average: 0.6897 (✅ ~0.69)
  Min: 0.5998 (✅ ~0.60)
  Max: 0.7801 (✅ ~0.78)
```

⚠️ **Yellow Light** (Check but may be OK):
```
public_training_properties: 5000 rows  (small dataset, but OK)
Offer Band Ratio Average: 0.71 (slightly high, but acceptable)
```

❌ **Red Light** (Fix required):
```
public_training_properties: 0 rows  (FAIL: no import)
public_training_labels: 0 rows      (FAIL: no labels)
Offer Band Ratio Average: 0.85      (FAIL: > 0.78 cap violated)
```

---

## Next Step After Verification

Once tables are populated:

1. ✅ Confirm row counts > 0
2. ✅ Confirm offer ratio in expected range
3. ✅ Move to replay step

```bash
$env:REPLAY_LIMIT="2000"
python services/api/tools/public_training/replay_wholesaling.py
```

Then paste wholesaling entrypoint details to wire the adapter.
