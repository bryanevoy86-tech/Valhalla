# NEXT: WIRE YOUR WHOLESALING ADAPTER

## Status

You now have:
- ✅ 4-step SANDBOX training pipeline (download → import → label → replay)
- ✅ Windows-native commands (PowerShell / cmd.exe)
- ✅ DB verification queries
- ✅ Go/No-Go safety gates (pursue rate, FP rate, offer bands)
- ✅ Phase 3.1 optional module concept (repair estimation)
- ✅ Golden tests for regression protection

**What's missing**: Connecting replay to your actual wholesaling logic (currently it defaults to "never pursue" — safe but uninformative).

---

## One-Shot Adapter Integration

When you provide the wholesaling entrypoint details, I will:

1. Write the exact import statement needed
2. Wire `run_wholesaling_pipeline()` to call your real scoring function
3. Update the adapter to handle your return format
4. Add any missing field mappings
5. Commit & you're ready to replay with REAL logic

**Time to wire**: 5 minutes  
**Risk**: None (still SANDBOX, APP_ENV gated)  
**Benefit**: Replay metrics become meaningful

---

## What I Need From You

### Option A: You Know the Path & Function Name

Paste (copy-paste from VS Code):

```
FILE PATH:    services/api/.../<filename>.py
FUNCTION:     <function_name>
RETURNS:      (what you know or can infer)
```

**Example**:
```
FILE PATH:    services/api/app/services/deals_scoring.py
FUNCTION:     evaluate_lead
RETURNS:      {"should_pursue": bool, "offer_low": float, "offer_high": float, "human_review_required": bool}
```

### Option B: You're Not Sure — Show Me What Exists

Paste directory listing:

```
services/api/
  ├── deals/
  │   ├── scoring.py
  │   ├── offer.py
  │   └── ...
  ├── app/
  │   ├── services/
  │   │   ├── lead_service.py
  │   │   ├── ...
  └── ...
```

Then tell me which ONE looks like where scoring/offer logic lives.

### Option C: Unsure What "Wholesaling Logic" Means

Tell me:
- "I have a function that takes a property address/ID and returns a decision"
- "I have a scoring model in [file]"
- "I use a router endpoint at [path]"
- "I don't have this yet"

I'll help you find it or create a simple placeholder.

---

## What the Adapter Does

**Before** (current — safe placeholder):
```python
def run_wholesaling_pipeline(lead: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "should_pursue": False,  # Always safe default
        "offer_low": None,
        "offer_high": None,
        "human_review_required": True
    }
```

**After** (wired to your logic):
```python
def run_wholesaling_pipeline(lead: Dict[str, Any]) -> Dict[str, Any]:
    # Import your actual logic
    from your_module import your_scoring_function
    
    # Call it with the lead data
    result = your_scoring_function(lead)
    
    # Return in the format replay expects
    return {
        "should_pursue": result.should_pursue,
        "offer_low": result.offer_low,
        "offer_high": result.offer_high,
        "human_review_required": result.human_review_required
    }
```

---

## After Wiring

You'll run:

```powershell
$env:APP_ENV="sandbox"
$env:DATABASE_URL="postgres://..."
$env:REPLAY_LIMIT="2000"

python services/api/tools/public_training/replay_wholesaling.py
```

And get real metrics like:

```
=== SANDBOX REPLAY REPORT (WHOLESALING) ===
Records replayed: 2000
Pursue rate: 8.2%        ← Your real pursue rate
Review rate: 91.8%       ← Your real review rate
Accuracy: 87.3%          ← How your scoring matches labels
Precision: 0.92          ← Quality of pursued deals
Recall: 0.78             ← Coverage of good deals
TP/FP/TN/FN: 150/13/1825/12
```

Then you check against [SANDBOX_REPLAY_GO_NO_GO_GATE.md](SANDBOX_REPLAY_GO_NO_GO_GATE.md) thresholds.

---

## Next Three Steps

### Step 1: Provide Wholesaling Entrypoint

Paste:
- File path (e.g., `services/api/app/services/lead_scoring.py`)
- Function name (e.g., `score_lead`)
- Any known details about what it returns

### Step 2: I Wire the Adapter

Takes ~5 min. Commit pushed automatically.

### Step 3: You Run Replay

Windows commands in [SANDBOX_TRAINING_QUICK_START.md](SANDBOX_TRAINING_QUICK_START.md)

Then decide: Metrics green → proceed to validation, or tighten thresholds first?

---

## What You Can Do Now (While Preparing)

1. **Verify pipeline setup** (if you have Render DB access):
   - Run download_sources.py
   - Run import_public_data.py
   - Check row counts (see [DB_VERIFICATION_GUIDE.md](DB_VERIFICATION_GUIDE.md))

2. **Locate your wholesaling logic**:
   - Search repo for "score", "offer", "pursue"
   - Find the function that decides whether to pursue a deal
   - Note the path + function name

3. **Test golden tests**:
   ```bash
   pytest tests/test_golden_wholesaling.py -v
   ```
   Should pass (will need tuning after adapter is wired).

---

## Ready?

**Paste your wholesaling entrypoint details** (file path + function name) and I'll wire it in one shot.

Once wired, the pipeline becomes:

**SANDBOX Training Pipeline + Real Scoring Logic = Meaningful Metrics**

Then you can confidently move toward LIVE validation.
