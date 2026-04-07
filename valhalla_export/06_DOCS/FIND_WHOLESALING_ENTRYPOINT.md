# FIND YOUR WHOLESALING ENTRYPOINT (5-Minute Search)

**When you're back at VS Code, use this guide to find the function you want replay to call.**

---

## Search Strategy (In Order)

Use **Ctrl+Shift+F** (Find in Files) for each search term.

### Search 1: "score"
```
score_lead
deal_score
scoring
lead_score
compute_score
score(
score_deal
```

**What to look for**: A function that takes a lead/property and returns a score or recommendation.

**Example result**:
```python
# services/api/deals/scoring.py
def score_lead(lead: dict) -> dict:
    return {"score": 75, "tier": "A", "reason": "Good location"}
```

---

### Search 2: "offer"
```
offer_band
offer_sheet
generate_offer
max_allowable_offer
mao (sometimes abbreviated)
create_offer
suggest_offer
```

**What to look for**: A function that generates an offer band or price recommendation.

**Example result**:
```python
# services/api/deals/offer_sheet.py
def generate_offer_band(property_value: float) -> dict:
    return {"offer_low": property_value * 0.60, "offer_high": property_value * 0.78}
```

---

### Search 3: "next_action"
```
next_action
recommend_action
route_next
decision
pursue
action_type
```

**What to look for**: A function that decides what action to take (pursue, review, reject).

**Example result**:
```python
# services/api/deals/next_action.py
def recommend_action(lead: dict) -> dict:
    return {
        "should_pursue": True,
        "next_action": "send_initial_offer",
        "human_review_required": True
    }
```

---

### Search 4: Known Locations (From Your Project Structure)

Based on mentions in your docs, search these specific files:

```
services/api/deals/
├── scoring/
│   ├── __init__.py
│   └── score_lead.py          ← Likely here
├── next_action/
│   ├── __init__.py
│   └── recommend.py           ← Or here
├── offer_sheet_router.py       ← Or here
├── summary_router.py           ← Or maybe here
└── scripts_service.py          ← Or here
```

**Fastest check**: Open each file and look for a function that:
- Takes `lead` or `property` or `deal` as input
- Returns a dict with score/offer/decision fields
- Has docstring or type hints

---

## What You're Looking For (Patterns)

### Pattern A: Scoring Function
```python
def score_lead(lead: dict) -> dict:
    # ... logic ...
    return {
        "score": int,
        "tier": str,
        "reasons": list
    }
```

### Pattern B: Decision Function
```python
def evaluate_opportunity(lead: dict) -> dict:
    # ... logic ...
    return {
        "should_pursue": bool,
        "confidence": float,
        "next_action": str
    }
```

### Pattern C: Offer Function
```python
def calculate_offer_band(property_value: float, condition: str) -> dict:
    # ... logic ...
    return {
        "offer_low": float,
        "offer_high": float
    }
```

### Pattern D: Combined (Best Case)
```python
def evaluate_wholesaling_opportunity(lead: dict) -> dict:
    # ... logic ...
    return {
        "should_pursue": bool,
        "offer_low": float,
        "offer_high": float,
        "human_review_required": bool,
        "score": int,
        "tier": str
    }
```

---

## Fallback: Quick Directory Scan

If searches aren't finding it:

```powershell
# PowerShell - list all Python files in deals
Get-ChildItem -Path "services/api/deals" -Recurse -Filter "*.py" | Select-Object FullName

# Then open each file and scan for "def " to see all functions
```

---

## Once You Find It: What to Paste

Format (exact):

```
FILE PATH:    services/api/deals/scoring/score_lead.py
FUNCTION:     score_lead
CALL EXAMPLE: score_lead({"address": "123 Main St", "assessed_value": 250000})
RETURNS:      {"should_pursue": true, "offer_low": 150000, "offer_high": 195000}
```

---

## Expected Results

✅ **Found it** - You'll see a function that clearly does scoring/offer/decision logic.

⚠️ **Multiple candidates** - Paste the one that returns the most complete info (score + offer + decision is best; just score is OK too).

❌ **Can't find it** - Paste your `services/api/deals/` folder listing and I'll tell you which file + function.

---

## What I'll Do Once You Provide It

Exact steps (no guessing):

1. **Read your function** (file path + name)
2. **Infer the payload format** from the function signature
3. **Map your return fields** to replay's expected format
4. **Write the adapter** (3-5 lines of code)
5. **Commit & test**

**Time**: ~5 minutes  
**Risk**: None (SANDBOX-only, no production changes)  
**Result**: Replay uses real wholesaling logic, metrics become meaningful

---

## Example Wiring (What I'll Do)

Before (safe placeholder):
```python
def run_wholesaling_pipeline(lead: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "should_pursue": False,
        "offer_low": None,
        "offer_high": None,
        "human_review_required": True
    }
```

After (example, if you provide scoring entrypoint):
```python
def run_wholesaling_pipeline(lead: Dict[str, Any]) -> Dict[str, Any]:
    from services.api.deals.scoring import score_lead
    
    result = score_lead(lead)
    
    return {
        "should_pursue": result.get("tier") in ("A", "B"),
        "offer_low": lead.get("assessed_value", 0) * 0.60,
        "offer_high": lead.get("assessed_value", 0) * 0.78,
        "human_review_required": True
    }
```

---

## Ready?

When you're at the computer:

1. **Ctrl+Shift+F** and search the terms above
2. **Find the function**
3. **Paste the details here**

Then I wire it and you replay with real logic.

No delays, no trial-and-error.
