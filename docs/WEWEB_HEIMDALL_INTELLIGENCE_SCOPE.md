# WeWeb Heimdall Intelligence Scope (Future Build)

**Status:** Design Document (Future Build, Not in First Launch)  
**Created:** 2026-04-13  
**Purpose:** Define future WeWeb pages for Heimdall Intelligence interaction (post-launch Phase 2+)

---

## Overview

**Timing:** Month 2 - Month 3 post-launch (AFTER Execution Console is stable)  
**Priority:** LOW (first WeWeb build is Execution Console only)  
**Scope:** Knowledge management and outcome recording UI  
**Breaking Changes:** ZERO (all additive)

---

## What This Is NOT

❌ NOT part of first WeWeb build  
❌ NOT required for launch  
❌ NOT blocking execution workflows  
❌ NOT autonomous services  

---

## What This IS

✅ Future capability design  
✅ Reference for Phase 2 development  
✅ Non-breaking UI additions  
✅ Operator helper tools  

---

## Phase 2+ UI: Heimdall Intelligence Pages (4 Pages)

### Page 1: Knowledge Base Dashboard

**Route:** `/heimdall/knowledge`  
**Access:** All roles (read-only for analysts, write for managers)  
**Purpose:** Browse and understand available knowledge

**Layout:**

```
┌─────────────────────────────────────────────────────────┐
│  📚 Knowledge Base                                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Search Box: "rehab cost"]  [Filter v]                │
│  Market: [Dropdown: ALL]  Strategy: [Dropdown: ALL]   │
│  Status: [Checkboxes: Trusted | Reviewed | Draft]    │
│                                                         │
│  KNOWLEDGE BASE (25 items)                             │
│  ┌─────────────────────────────────────────────────┐ │
│  │ ✓ Rehab Cost Trends Q1 2026                     │ │
│  │   Market: Memphis    Strategy: Wholesale, Flip  │ │
│  │   Confidence: ████████░░ 0.88                  │ │
│  │   Status: TRUSTED  Source: Market Report       │ │
│  │   [View Details] [View Insights] [Edit Status]  │ │
│  └─────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─────────────────────────────────────────────────┐ │
│  │ ⭘ Seller Negotiation Patterns                  │ │
│  │   Market: Memphis    Strategy: Wholesale        │ │
│  │   Confidence: ███████░░░ 0.75                  │ │
│  │   Status: REVIEWED  Source: Operator Note      │ │
│  │   [View Details] [View Insights] [Edit Status]  │ │
│  └─────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─────────────────────────────────────────────────┐ │
│  │ ◉ Market Trend - Tech Relocation               │ │
│  │   Market: Nashville  Strategy: Hold             │ │
│  │   Confidence: ████░░░░░░ 0.55                  │ │
│  │   Status: DRAFT  Source: Public Forum           │ │
│  │   [View Details] [Need Review] [Approve]        │ │
│  └─────────────────────────────────────────────────┘ │
│                                                         │
│  [← Previous] [1 2 3 4 5] [Next →]                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Interactions:**
- Search by keyword
- Filter by market, strategy, status, confidence level
- View full knowledge item (raw + summary)
- See list of insights extracted
- Update status (draft → reviewed → trusted)
- Add tags or notes
- Deprecate obsolete knowledge

---

### Page 2: Add Knowledge (Modal or Dedicated Page)

**Route:** `/heimdall/add-knowledge` or modal from dashboard  
**Access:** Managers, Analysts, Knowledge admins  
**Purpose:** Ingest new knowledge from sources

**Layout:**

```
┌─────────────────────────────────────────────────────────┐
│  ➕ Add Knowledge Item                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  STEP 1: SELECT SOURCE (or create new)                │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Select Existing Source:                         │ │
│  │ [Dropdown: Memphis Market Report ▼]             │ │
│  │                          OR                     │ │
│  │ Create New Source:                              │ │
│  │ Source Name: [___________________]             │ │
│  │ Source Type: [market_report ▼]                │ │
│  │ Trust Level: [high ▼]                          │ │
│  │ URL: [___________________]                     │ │
│  └─────────────────────────────────────────────────┘ │
│                                                         │
│  STEP 2: ENTER KNOWLEDGE                              │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Title: [_________________________]              │ │
│  │                                                 │ │
│  │ Knowledge Type: [rehab_cost ▼]                │ │
│  │                                                 │ │
│  │ Market: [memphis ▼]                           │ │
│  │ Strategy: [wholesale ☑] [flip ☑] [hold ☐]   │ │
│  │ Asset Type: [single_family ▼]                │ │
│  │                                                 │ │
│  │ Full Content:                                   │ │
│  │ ┌────────────────────────────────────────────┐ │ │
│  │ │ [Paste full text from source here]         │ │ │
│  │ │                                            │ │ │
│  │ │ Bathroom rehabs in Q1 2026 range...        │ │ │
│  │ └────────────────────────────────────────────┘ │ │
│  │                                                 │ │
│  │ Summary: [or auto-generate from content]        │ │
│  │ ┌────────────────────────────────────────────┐ │ │
│  │ │ Bathroom: $26-32k, Kitchen: $35-45k...    │ │ │
│  │ └────────────────────────────────────────────┘ │ │
│  │                                                 │ │
│  │ Confidence Score: ■■■■■■■■░░ 0.85            │ │
│  │                                                 │ │
│  │ Tags: [cost_driven] [seasonal] [+]             │ │
│  └─────────────────────────────────────────────────┘ │
│                                                         │
│  [← Back] [Save as Draft] [Publish]                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Source selection or creation
- Full-form knowledge entry
- Auto-summary generation (future: LLM)
- Category selection
- Confidence slider
- Tag management
- Save as draft or publish immediately

---

### Page 3: Record Outcome & Extract  Lessons

**Route:** `/heimdall/record-outcome`  
**Access:** All operators  
**Purpose:** Record deal results and extract lessons

**Layout:**

```
┌─────────────────────────────────────────────────────────┐
│  📊 Record Outcome & Learn                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  SELECT DEAL                                           │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Deal ID: [DEAL_2026_04_001 ▼]                 │ │
│  │ Case ID: [CASE_123]                            │ │
│  │ Market: [Memphis] Strategy: [Wholesale]        │ │
│  └─────────────────────────────────────────────────┘ │
│                                                         │
│  COMPARISON: PREDICTED vs ACTUAL                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │                  PREDICTION | ACTUAL  | DELTA  │ │
│  │ ARV         | $185,000     | $188k  | +$3k   │ │
│  │ Rehab Cost  |  $30,000     | $37.5k | +$7.5k │ │
│  │ Close Days  |  18          |  32    | +14 d  │ │
│  │ Total Profit| $15,000      | $8.5k  | -$6.5k │ │
│  │ ROI %       |   35%        |  22%   | -13pp  │ │
│  └─────────────────────────────────────────────────┘ │
│                                                         │
│  WHAT DID WE LEARN?                                    │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Narrative (optional):                            │ │
│  │ ┌────────────────────────────────────────────┐ │ │
│  │ │ Contractor overcharge; found hidden        │ │ │
│  │ │ electrical issues. Bathroom work was       │ │ │
│  │ │ 26% higher than estimate.                  │ │ │
│  │ └────────────────────────────────────────────┘ │ │
│  │                                                 │ │
│  │ Key Lesson:                                     │ │
│  │ ┌────────────────────────────────────────────┐ │ │
│  │ │ Bathroom costs consistently underestimated.│ │ │
│  │ │ Recommend +20% baseline for Q2.            │ │ │
│  │ └────────────────────────────────────────────┘ │ │
│  │                                                 │ │
│  │ Applies To:                                     │ │
│  │ Market: [Memphis ▼]                            │ │
│  │ Strategy: [wholesale ☑] [flip ☑]             │ │
│  │ Asset Type: [single_family ▼]                 │ │
│  │                                                 │ │
│  │ Confidence in Lesson: ████████░░ 0.78         │ │
│  └─────────────────────────────────────────────────┘ │
│                                                         │
│  [Cancel] [Save Outcome] [Save + Extract Lesson]      │
│                                                         │
│  [If success] ✓ Outcome recorded. 47 outcomes in DB.  │
│               ✓ Lesson confidence adjusted (0.78)      │
│               ✓ Updated market memory snapshot.        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Select deal from closed cases
- Side-by-side predicted vs actual display
- Auto-calculate deltas
- Free-form narrative for context
- Structured lesson extraction
- Applicability scoping
- Confidence adjustment UI

---

### Page 4: Market Memory & Recommendations

**Route:** `/heimdall/market-memory`  
**Access:** All roles (read-only)  
**Purpose:** View aggregated market insights and recommendations

**Layout:**

```
┌─────────────────────────────────────────────────────────┐
│  🧠 Market Memory Snapshot                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  SELECT MARKET & STRATEGY                              │
│  Market: [Memphis ▼]                                   │
│  Strategy: [Wholesale ▼]    [View all strategies]      │
│  Asset Type: [Single Family ▼]                         │
│  [Generate Snapshot]                                   │
│                                                         │
│  ════════════════════════════════════════════════════ │
│                                                         │
│  MARKET INSIGHTS (Based on 47 deals + 23 knowledge)   │
│  ┌─────────────────────────────────────────────────┐ │
│  │ KEY METRICS                                     │ │
│  │ • Avg Rehab Cost: $34,500 (confidence: 0.92)   │ │
│  │ • Seller Reduces: 3.6% on 2nd offer (0.88)    │ │
│  │ • Target ARV Accuracy: 98% (confidence: 0.85)  │ │
│  │ • Avg Days to Close: 32 days (0.80)            │ │
│  │ • Profit Margin Reality: 8.2% (was 12% est)   │ │
│  │                                                 │ │
│  │ TOP INSIGHTS                                    │ │
│  │ 1. Bathroom work consistently +22-27%           │ │
│  │    (from 12 deals; confidence: 0.91)           │ │
│  │                                                 │ │
│  │ 2. New contractors need +15% buffer             │ │
│  │    (from 3-deal pattern; confidence: 0.78)     │ │
│  │                                                 │ │
│  │ 3. Close times trending +8% this quarter        │ │
│  │    (market heating up; confidence: 0.65)       │ │
│  │                                                 │ │
│  │ RECENT OUTCOMES (Last 5 Deals)                 │ │
│  │ Deal 2026-04-047: Profit +$2k vs predict       │ │
│  │ Deal 2026-04-046: Profit -$1.5k vs predict     │ │
│  │ Deal 2026-04-045: Profit -$3.2k vs predict     │ │
│  │ Deal 2026-04-044: Profit -$4.8k vs predict     │ │
│  │ Deal 2026-04-043: Profit +$1.2k vs predict     │ │
│  └─────────────────────────────────────────────────┘ │
│                                                         │
│  ════════════════════════════════════════════════════ │
│                                                         │
│  RECOMMENDATIONS FOR NEW DEALS                         │
│  "For wholesale single-family in Memphis:"             │
│                                                         │
│  ✓ Assume $34.5k rehab budget (not $30k)              │
│    Confidence: HIGH (0.92) - Based on 47 deals        │ │
│    Range: $32k - $37k (typical variance)              │ │
│    Reliability: All recent bathroom work 28-38k       │ │
│                                                         │
│  ✓ Expect seller to reduce 3.6% on 2nd offer         │ │
│    Confidence: HIGH (0.88) - Pattern across 40+ deals │ │
│    Range: 2.1% to 5.1% (but 90% hit 3-4% range)      │ │
│    Note: Distressed properties may not negotiate     │ │
│                                                         │
│  ✓ Plan for 32-35 day close (not 18 days)            │ │
│    Confidence: MEDIUM (0.80) - Trending longer        │ │
│    Market heating; hold for 35+ days conservatively   │ │
│                                                         │
│  ≈ Profit reality: 8-10% margin (not 15%)             │ │
│    Confidence: HIGH (0.90) - 47-deal average shows   │ │
│    Pattern: High estimate bias of 35-45%; adjust      │ │
│                                                         │
│  ════════════════════════════════════════════════════ │
│                                                         │
│  DATA PROVENANCE                                       │ │
│  Total Knowledge Items: 18                            │ │
│  Total Deals Recorded: 47                             │ │
│  Data Sources: Memphis Market Report, Operator Notes  │ │
│  Last Updated: 2026-04-13 15:23 UTC                  │ │
│  Quality Score: 0.88                                  │ │
│                                                         │ │
│  [📥 Download Snapshot] [📊 View Trends] [📋 Export] │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Market snapshot generation
- Key metrics dashboard
- Recent outcomes list
- Data-backed recommendations
- Confidence scoring
- Trend analysis
- Data provenance transparency
- Export/download capability

---

## Build Phases for WeWeb Heimdall

### Phase 1 (Now - Week 1-2)
Nothing - focus on Execution Console

### Phase 2 (Week 3+, after console stable)
✅ Deploy Knowledge Base Dashboard (read-only)  
✅ Add "Record Outcome" button  
✅ Basic market memory view  

### Phase 3 (Month 1+)
✅ Full outcome recording UI  
✅ Lesson extraction form  
✅ Knowledge adding capability  

### Phase 4 (Month 2+)
✅ Advanced market memory insights  
✅ Trend analysis and forecasting  
✅ Team knowledge sharing  

---

## Routes Needed

All routes already defined in Phase 6 router:

```
GET    /heimdall/intelligence/sources
POST   /heimdall/intelligence/sources
GET    /heimdall/intelligence/items
POST   /heimdall/intelligence/items
GET    /heimdall/intelligence/items/{item_id}
GET    /heimdall/intelligence/items/{item_id}/insights
POST   /heimdall/intelligence/items/{item_id}/insights
POST   /heimdall/intelligence/search
POST   /heimdall/intelligence/recommend
POST   /heimdall/intelligence/outcomes
GET    /heimdall/intelligence/outcomes
POST   /heimdall/intelligence/outcomes/{outcome_id}/lesson
GET    /heimdall/intelligence/market-memory
```

---

## Design Considerations

✅ **Mobile-Friendly:** All pages responsive to tablet/mobile  
✅ **Read Most, Write Seldom:** Dashboard read-heavy; write flows simple  
✅ **Offline Awareness:** Can cache market snapshot locally  
✅ **Safety:** All write operations confirmable  
✅ **Accessibility:** High contrast, keyboard navigation  
✅ **Performance:** Data cached where sensible  

---

## Not Included (Scope Protection)

❌ Real-time market scraping  
❌ Autonomous recommendations  
❌ Community knowledge sharing (maybe future)  
❌ Advanced ML visualizations (maybe future)  
❌ Third-party data integrations (maybe future)

---

## Success Criteria

✅ Team records 80%+ of closed deals within 2 weeks of close  
✅ Knowledge base reaches 50+ items by month 2  
✅ Market memory accuracy within 5% of realized outcomes  
✅ Team reports feeling "guided" by Heimdall in 30%+ of decisions  
✅ Zero performance impact on execution console  

---

## Next: Implementation

This scope is ready for WeWeb team when:
1. Execution Console is stable and launched
2. First 20+ deals have been recorded
3. Initial lessons have been extracted
4. Team is comfortable with outcome recording flow

**NOT blocking first WeWeb launch.**  
**Ready for Phase 2 discussions.**
