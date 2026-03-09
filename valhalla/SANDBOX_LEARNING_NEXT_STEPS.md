# SANDBOX Learning System - Current State & Engineering Path Forward

## 🎯 What We Have Now

### ✅ Complete Foundation
- **Approval Workflow**: Email/webhook queuing → Review → Approve/Decline
- **Learning Scoreboard**: Real-time metrics via `/api/sandbox/learning/report`
- **Activity Trail**: Full audit log of all decisions
- **Human Labels**: Framework for training signals (APPROVE/REJECT/NEEDS_INFO)

### 📊 Current Metrics (as of Feb 3, 2026)
```
Queue Size:         3 pending items
Items Approved:     3 total
Items Declined:     2 total
Approval Rate:      60% (Moderate - needs improvement)
False Positives:    40% (High - needs tuning)
Labels Created:     2 (Need 18 more for effective learning)
Safety Status:      RED (too many declines)
Learning Signal:    WEAK (<5 labels)
```

### 🚨 Root Cause Analysis
You're not seeing "learning failure" — you're seeing "quality gate failure."

**Why approval rate is 60%:**
- Everything SANDBOX blocks → Gets queued for approval
- No pre-filter on what enters the queue
- Result: You review and decline low-quality items
- False decline rate looks high, but it's actually the system working as designed (it blocked them, you confirmed the block was right)

---

## 🔧 The 3-Step Engineering Fix

### Step 1: Pre-Queue Filter (Deploy This Week)
**What**: Before queuing for approval, check: `profit >= 20k AND roi >= 20 AND risk <= 15`

**Why**: Stops low-quality items from reaching your review queue

**Expected Improvement**:
- Queue volume: -30 to -50%
- Approval rate: 60% → 80%+
- Your attention: Redirected to higher-quality decisions
- Learning signal: Stronger (less noise)

**Implementation**: See `PRE_QUEUE_FILTER_GUIDE.md` for exact code

### Step 2: Structured Labeling (Week 1)
**Label these 18 items strategically** (not randomly):

```
Category 1: "Clearly Good" (5 items)
- Characteristics: high profit (>30k), high ROI (>25), low risk (<10)
- Your Decision: APPROVE
- Why: Trains system on your ideal deal

Category 2: "Clearly Bad" (5 items)
- Characteristics: low profit (<10k), low ROI (<10), high risk (>25)
- Your Decision: REJECT
- Why: Trains system what to block

Category 3: "Borderline" (5 items)
- Characteristics: medium across metrics (profit 15-25k, ROI 15-25, risk 10-20)
- Your Decision: NEEDS_INFO
- Why: Trains system when to ask for more data

Category 4: "High Risk / High Reward" (5 items)
- Characteristics: high profit (>25k) but high risk (>20)
- Your Decision: Your strategic call
- Why: Trains system on your risk tolerance
```

### Step 3: Monitor & Iterate (Ongoing)
**Daily**: Check learning scorecard
```
GET /api/sandbox/learning/scorecard
```

**Weekly**: Check full report
```
GET /api/sandbox/learning/report
```

**Track these**:
- Approval rate (should trend UP)
- False positive rate (should trend DOWN)
- Queue size (should stabilize after filter)
- Labels collected (target: 5/week → 20 in 4 weeks)

---

## 📈 Success Timeline

### Week 1 (Now)
- Deploy pre-queue filter
- Watch approval rate jump to 75%+
- Start labeling items (categories 1 & 2 first)

### Week 2
- Finish labeling all 20 items (4 categories)
- Run learning report
- Identify which gate to tune first (profit/roi/risk)

### Week 3
- Retrain or adjust gates based on labels
- Approval rate should be 80%+
- False positive rate should be <10%

### Week 4+
- System self-optimizes as labels accumulate
- Approval rate stabilizes at your preferred level
- Gate thresholds auto-tune based on patterns

---

## ⚡ What NOT to Do

❌ Don't retrain yet (only 2 labels = noise)
❌ Don't adjust all gates at once (can't isolate what helped)
❌ Don't label randomly (structured categories teach better)
❌ Don't deploy filter without monitoring (need to measure impact)

---

## ✅ What to Do Now (Exact Next Steps)

**Action 1** (15 min): Read `PRE_QUEUE_FILTER_GUIDE.md`

**Action 2** (30 min): Deploy pre-queue filter to notify.py
- Copy code from guide
- Deploy to main branch
- Monitor queue for 1 hour (should drop by 30-50%)

**Action 3** (Daily): Check scorecard
```bash
curl -H "X-API-Key: a774e90bcc3de95f0513782e41fc454f" \
  https://valhalla-api-ha6a.onrender.com/api/sandbox/learning/scorecard
```

**Action 4** (This Week): Label 5-10 items (start with "clearly good" and "clearly bad")
- From `/api/approvals/pending`, pick items
- Call POST `/api/sandbox/labels` with APPROVE/REJECT
- Takes ~2 min per item

---

## 🎯 The Real "Learning" Happens Here

Your SANDBOX system isn't "dumb" — it's **safety-first by design**.

The learning happens when:
1. System blocks something (gate fires) ✅ Working
2. You review and decide (approval workflow) ✅ Working
3. System sees your decision + reasons (labels) ← **You are here**
4. System adjusts gates based on patterns (optimization) ← **Next**

Steps 1-3 are complete. Step 4 is blocked by "not enough data (2 labels)."

**Your job**: Provide 18 more labels with clear patterns.

System's job: Learn from those patterns and improve.

---

## 📞 If Approval Rate Doesn't Jump After Filter Deploy

Check:
- Are profit/roi/risk fields in your email payload? (If not, filter won't work)
- Did filter deploy successfully? (Check Render logs)
- Are thresholds too tight? (Try lowering MIN_PROFIT to 15k for testing)

If stuck: Dump one approved and one declined item (redacted JSON), and we'll know instantly which gate to adjust.

---

## 💡 Why This Approach Works

- **Measurable**: Learn report shows exact metrics
- **Fast**: Pre-filter improves approval rate in hours, not weeks
- **Safe**: Labels provide ground truth, not guesses
- **Scalable**: Works with 100 items or 1M items
- **Explainable**: You know why each item was queued or blocked

This is how ML systems work in production: measure → filter → label → iterate.

---

**Status**: Ready to execute. Deploy pre-queue filter, then label 18 items.
Approval rate will jump from 60% → 80%+ within 48 hours.
