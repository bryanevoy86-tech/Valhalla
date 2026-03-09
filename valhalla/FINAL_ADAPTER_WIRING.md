# IMMEDIATE: Wire Adapter (Final Step)

**Goal**: Find your wholesaling entrypoint, wire it, and get real metrics.

---

## Step 1: Verify Training Data Is Loaded

### Option A: SQL Query (Fast)

Run in your PostgreSQL client:
```sql
SELECT COUNT(*) as prop_count FROM public_training_properties;
SELECT COUNT(*) as label_count FROM public_training_labels;
```

**Expected**: Both > 0 (if 0, re-run import_public_data.py first)

### Option B: Python Check (No DB Client Needed)

```powershell
# Create temp check script
@"
import os
from sqlalchemy import create_engine, text

db = os.environ.get("DATABASE_URL")
if not db:
    print("ERROR: DATABASE_URL not set")
    exit(1)
engine = create_engine(db, future=True)
with engine.begin() as conn:
    a = conn.execute(text("SELECT COUNT(*) FROM public_training_properties")).scalar()
    b = conn.execute(text("SELECT COUNT(*) FROM public_training_labels")).scalar()
print(f"public_training_properties: {a}")
print(f"public_training_labels: {b}")
"@ | Out-File -FilePath "services/api/tools/public_training/db_check.py" -Encoding UTF8

# Run it
python services/api/tools/public_training/db_check.py
```

**Expected output**:
```
public_training_properties: 45237
public_training_labels: 45237
```

---

## Step 2: Find Your Wholesaling Entrypoint (2 Minutes)

### Search Option 1: PowerShell (Built-in, No Tools Needed)

```powershell
# From repo root, search for scoring/offer/decision functions
Select-String -Path "services\api\**\*.py" `
  -Pattern "score_lead|deal_score|scoring|offer_band|offer_sheet|generate_offer|mao|max_allowable_offer|next_action|recommend_action|disposition|wholesale" `
  -CaseSensitive:$false | Select-Object -First 30
```

This will show file paths + line numbers where these keywords appear.

### Search Option 2: If you have `rg` (ripgrep)

```powershell
rg -n "score_lead|deal_score|scoring|offer_band|offer_sheet|generate_offer|mao|max_allowable_offer|next_action|recommend_action|disposition|wholesale" services/api
```

### Search Option 3: Manual Directory Browse (Slowest)

Open these folders and look for `.py` files with likely names:
```
services/api/deals/
services/api/app/services/
services/api/app/routers/
```

Look for files containing "score", "offer", "deal", "wholesale", or "next_action".

---

## Step 3: Identify the Best Candidate

You're looking for a **function** (not a class, not a route) that:

✅ Takes a `lead` or `property` or `deal` dict as input  
✅ Returns a dict with one or more of:
  - `score`, `tier`, `reasons`
  - `should_pursue`, `decision`, `next_action`
  - `offer_low`, `offer_high`, `mao`, `offer_band`

**Example Good Matches**:
```python
def score_lead(lead: dict) -> dict:
    # returns {"score": 75, "tier": "A"}

def evaluate_opportunity(lead: dict) -> dict:
    # returns {"should_pursue": True, "offer_low": 150000}

def get_next_action(deal: dict) -> dict:
    # returns {"next_action": "send_offer", "review_required": True}
```

---

## Step 4: Open the File and Copy the Function Signature

Once you find a candidate, open the file and find the function definition.

**Copy the signature and first few lines** so I can see:
- Function name
- Parameter names / types (if typed)
- What it returns (look for `return {` statements)

---

## Step 5: Paste the Details HERE

Once you've found it, paste:

```
FILE PATH: services/api/deals/scoring.py
FUNCTION:  score_lead
SAMPLE RETURN: (paste one example return dict if you see it, or just say "returns dict with score/tier")
```

Or if you got multiple search results and want me to narrow it down:

```
Paste the search output (top 20-30 lines showing file paths + line numbers)
```

---

## After You Paste

I will:

1. **Read the function signature** from the file you specify
2. **Understand what it expects** (lead dict fields)
3. **Understand what it returns** (score? offer? decision?)
4. **Write the adapter** that:
   - Converts training lead → your function's input format
   - Calls your real function
   - Maps output → replay's expected format
5. **Commit to main**
6. **You run replay** with real logic

---

## Timeline

| Step | Time | Who |
|------|------|-----|
| Verify DB | 1 min | You (SQL or Python) |
| Find function | 2 min | You (search) |
| Paste details | 1 min | You (copy/paste) |
| Wire adapter | 5 min | Me (write + commit) |
| Run replay | 2 min | You (execute) |
| Check metrics | 5 min | You (compare to gates) |
| **TOTAL** | **~15 min** | |

---

## Ready?

1. **Run the DB check** (make sure tables have data)
2. **Search for your scoring/offer/decision function**
3. **Paste the FILE PATH + FUNCTION name** here

Then I wire it and you replay with real data.

No ambiguity, no delays.
