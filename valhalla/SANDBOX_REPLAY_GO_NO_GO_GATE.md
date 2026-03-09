# GO/NO-GO GATE: SANDBOX TRAINING REPLAY THRESHOLDS

**Purpose**: Define safe decision criteria before tightening wholesaling behavior toward LIVE Manitoba launch.

**Status**: SANDBOX only. These thresholds prevent "overconfident automation" — the #1 failure mode.

---

## Safety Thresholds (Minimum Safe Before LIVE)

### Metric Targets

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| **Pursue Rate** | ≤ 10% | Conservative; default is reject |
| **Review Rate** | ≥ 80% | Until rules are proven, flag for human |
| **False Positive Rate** | Near 0% on high-risk segment | Avoid pursuing low-value junk |
| **Offer_high** | Never > 78% of assessed value | Cap conservatively |
| **Golden Tests** | 100% pass | Regression = blocker |

### Detailed Rules

#### 1. **Pursue Rate ≤ 10%**
- If replay shows > 10% of deals flagged "pursue" → TIGHTEN thresholds before considering LIVE
- Low pursue rate is safe (you reject most deals)
- High pursue rate requires proof that deals are real + profitable

**Action if exceeded**: Edit `generate_synthetic_outcomes.py` constants:
```python
HIGH_RISK_ASSESSMENT_CEILING = 150000  # Raise to reject more low-value
MAX_OFFER_TO_ASSESSMENT = 0.70         # Lower offer cap
```
Re-run label generation + replay.

#### 2. **Review Rate ≥ 80%**
- Desired: Most deals flagged for human check (safe default)
- Minimum: Never drop below 80% until you have proven metrics
- Review-gating prevents rogue automation

**Action if below 80%**: Increase `human_review_required` flag in label generation.

#### 3. **False Positive Rate Near 0%** 
- False Positive = Predicted "pursue" but labeled "don't pursue"
- On high-risk segment (< $120k), FP should be essentially zero
- Indicates your scoring logic is not conflicting with risk rules

**Calculation**:
```
FP / (FP + TP) should be < 0.05 (5% or less)
```

**Action if exceeded**: Review your wholesaling thresholds — you're pursuing deals marked high-risk.

#### 4. **Offer_high Never > 78% of Assessed Value**
- Hard cap during training (conservative)
- This prevents over-offering in early stage
- Once metrics prove good, you can raise to 82% (still conservative)

**Check in replay output**:
```sql
SELECT MAX(offer_high / assessed_value) as max_offer_ratio
FROM public_training_labels
WHERE should_pursue = true;
```

Should be ≤ 0.78. If > 0.78 → Fix label generator.

#### 5. **Golden Tests Must Pass 100%**
```bash
pytest tests/test_golden_wholesaling.py -v
```

**Expected**: ✅ All tests pass  
**If fail**: Indicates unintended behavior change. Fix before proceeding.

---

## Decision Matrix

### Scenario 1: All Metrics Green
```
Pursue rate: 8% ✅
Review rate: 92% ✅
FP rate: 2% ✅
Offer_high ratio: 0.77 ✅
Golden tests: 100% pass ✅

→ **GO**: Safe to consider next iteration
```

### Scenario 2: Pursue Rate Too High
```
Pursue rate: 15% ❌ (> 10%)
Review rate: 70% ❌ (< 80%)
FP rate: 12% ❌

→ **NO-GO**: Tighten thresholds + re-run pipeline
```

### Scenario 3: Golden Tests Fail
```
test_golden_cases: FAILED ❌

→ **NO-GO**: Understand what changed, roll back or fix behavior
```

### Scenario 4: Offer Band Violated
```
Offer_high ratio: 0.82 ❌ (> 0.78)

→ **NO-GO**: Check label generation, fix offer cap
```

---

## Replay Report Template

When you run replay, you'll get output like this:

```
=== SANDBOX REPLAY REPORT (WHOLESALING) ===
Records replayed: 2000
Pursue rate: 8.2%
Review rate: 91.8%
Accuracy (where labeled): 87.3%
Precision: 0.92
Recall: 0.78
TP/FP/TN/FN: 150/13/1825/12
==========================================
```

**Interpretation**:
- **Pursue rate 8.2%**: ✅ Under 10% (safe)
- **Review rate 91.8%**: ✅ Over 80% (safe)
- **Precision 0.92**: Of deals pursued, 92% match labels (good)
- **Recall 0.78**: Found 78% of actually-good deals (reasonable)
- **FP = 13**: 13 false positives out of 1825 negatives = 0.7% FP rate ✅

**Verdict**: GO (metrics are green)

---

## Phase Progression

### Phase 3 (Current): SANDBOX with Conservative Defaults
- Pursue rate: 0% (safe fallback)
- Review rate: 100%
- All deals flagged for human check
- **No real-world impact**

### Phase 3.1 (Optional): Wire Real Logic + Tighten Thresholds
- Pursue rate: up to 10% (proven safe)
- Review rate: stays ≥ 80%
- Metrics-driven tuning
- **Still SANDBOX, but with real signals**

### Phase 4 (Future): Manitoba LIVE Launch
- Pursue rate: 5–15% (data-proven)
- Review rate: ≥ 70% (human-in-loop)
- Offer bands tightened based on 6-week SANDBOX data
- **Real-world execution begins**

---

## Preventing Overconfident Automation

This gate structure prevents the #1 failure mode:

❌ **Bad**: "Our model says pursue. Let's do 1000 outreach calls."  
✅ **Good**: "Replay shows 8% pursue rate, metrics green. Small batch test first."

---

## What Gets Updated

When you wire the wholesaling adapter (next step), these gates become **real**:
- Replay uses your actual scoring logic (not safe placeholder)
- Metrics reflect your business rules
- Golden tests will likely need tuning to match real behavior
- Thresholds may need adjustment based on your deal quality

**You provide**: Wholesaling entrypoint path + function name  
**I wire**: Adapter to use real logic  
**You check**: Metrics against these thresholds  
**Decision**: Proceed to Phase 3.1 or tighten rules

---

## Next Step

Paste your wholesaling entrypoint details:
1. File path (e.g., `services/api/deals/scoring.py`)
2. Function name (e.g., `score_lead`)
3. Any known imports or dependencies

Then I'll wire the adapter and you'll run replay with real data.
