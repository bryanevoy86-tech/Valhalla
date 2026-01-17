# DB-8 — Offer Sheet Builder v1

**Status:** ✅ COMPLETE  
**Files Created:** 2  
**Routers Wired:** 1  
**Endpoints:** 1  
**Total Deal Bank Now:** DB-0 through DB-8 (10 components, 14 endpoints)

---

## Overview

**Offer Sheet Builder v1** transforms a scored deal into actionable offer guidance:
- Pricing tiers (low/target/high based on MAO)
- Terms guidance (earnest money, inspection days, close timeline)
- Seller psychology (angle by motivation level)
- Objections playbook (3 common objections + responses)
- Follow-up cadence (varies by Cone band)
- Wholesale disposition checklist
- Cone band restrictions (no escalation if C/D)

---

## Endpoint

### GET /core/deals/{deal_id}/offer_sheet

**Request:**
```bash
curl "http://localhost:4000/core/deals/{deal_id}/offer_sheet"
```

**Response Example (High-Motivation CA Wholesale Deal):**
```json
{
  "deal_id": "uuid-123",
  "band": "A",
  "currency": "CAD",
  "inputs": {
    "asking_price": 350000,
    "arv": 500000,
    "est_repairs": 40000,
    "strategy": "wholesale",
    "seller_motivation": "high",
    "stage": "new"
  },
  "score": {
    "score": 82,
    "equity_pct": 30.0,
    "mao_suggested": 280000.00,
    "flags": []
  },
  "offer_guidance": {
    "low_offer": 257600.00,
    "target_offer": 280000.00,
    "high_offer": 288400.00,
    "earnest_money": 500,
    "inspection_days": 7,
    "close_days_target": 14
  },
  "seller_angle": "Speed + certainty. Emphasize clean close, less hassle, flexible timeline.",
  "objections": [
    {
      "objection": "Your offer is too low",
      "response": "I'm pricing in repairs/holding costs and risk. If we confirm repair scope together, I can revisit numbers."
    },
    {
      "objection": "I need to think",
      "response": "Totally fair. What's the main thing you need clarity on—price, timeline, or process? I'll answer that and give you space."
    },
    {
      "objection": "Someone else offered more",
      "response": "That may be true. My advantage is certainty and speed. If they can't close, I can. Do you want a guaranteed close or a maybe?"
    }
  ],
  "follow_up_cadence": [
    {
      "when": "today",
      "action": "call_or_text",
      "note": "Confirm motivation, timeline, condition."
    },
    {
      "when": "24h",
      "action": "follow_up",
      "note": "Re-ask decision blocker; offer solution."
    },
    {
      "when": "72h",
      "action": "follow_up",
      "note": "Schedule walkthrough / collect photos / finalize offer."
    },
    {
      "when": "7d",
      "action": "nurture",
      "note": "Soft touch. Keep relationship."
    }
  ],
  "disposition": {
    "buyer_type": "cash/investor",
    "package_needed": [
      "address (if available)",
      "photos",
      "repair estimate",
      "ARV comps summary",
      "access window"
    ],
    "disclaimer": "Do not market as MLS. Use compliant language and assignable contract rules."
  },
  "restrictions": [],
  "notes": [
    "Offer sheet is advisory only; you approve final numbers and terms.",
    "Tune MAO heuristics per province/state later (KV + underwriting packs)."
  ]
}
```

---

## Response Structure

### Core Fields
- **deal_id:** Deal identifier
- **band:** Current Cone band (A/B/C/D)
- **currency:** CAD or USD based on country

### Inputs (Echo)
- **asking_price:** Original asking price
- **arv:** After-repair value
- **est_repairs:** Estimated repair cost
- **strategy:** wholesale|brrrr|flip|rental
- **seller_motivation:** high|medium|low|unknown
- **stage:** Current pipeline stage

### Score (From DB-4)
- **score:** 0–100
- **equity_pct:** Equity percentage
- **mao_suggested:** Max allowable offer (MAO)
- **flags:** Red flags (if any)

### Offer Guidance (Computed)
- **low_offer:** Conservative offer (92% of MAO, or anchored to asking if lower)
- **target_offer:** Recommended offer (MAO-based)
- **high_offer:** Maximum offer (103% of MAO)
- **earnest_money:** CAD 500 / USD 1,000
- **inspection_days:** 7 days
- **close_days_target:** 14 (high motivation) or 21 (medium/low)

### Seller Angle (Motivation-Based)
- **High:** "Speed + certainty. Emphasize clean close, less hassle, flexible timeline."
- **Medium:** "Certainty + convenience. Emphasize solutions, options, painless process."
- **Low/Unknown:** "Information + rapport. Ask questions, qualify gently, avoid pushing."

### Objections Playbook (v1)
3 common objections with suggested responses:
1. "Your offer is too low" → Explain repairs/risk, offer to revisit with confirmed scope
2. "I need to think" → Qualify what decision blocker, offer space
3. "Someone else offered more" → Emphasize certainty vs maybe, point to your speed

### Follow-Up Cadence
**Bands A/B (Expansion/Caution):**
- Today: Call or text (confirm motivation, timeline, condition)
- 24h: Follow-up (re-ask blocker, offer solution)
- 72h: Follow-up (walkthrough, photos, finalize offer)
- 7d: Nurture (soft touch, keep warm)

**Bands C/D (Stabilization/Survival):**
- Today: Light contact (confirm basics, no pressure)
- 48h: Follow-up light (ask if questions, keep warm)

### Disposition (Wholesale Only)
- **buyer_type:** "cash/investor"
- **package_needed:** List of materials for buyer presentation
- **disclaimer:** Compliance note on MLS + assignable contract rules

### Restrictions
- **Band C/D:** "Do not escalate. Use light contact + data gathering only."
- **Band B + opportunistic engines:** "Cannot scale (note: not relevant for deals)."

### Notes
- "Offer sheet is advisory only; you approve final numbers and terms."
- "Tune MAO heuristics per province/state later (KV + underwriting packs)."

---

## Logic Overview

### Offer Ranges
```
If MAO = $250,000:
  low_offer = 250,000 × 0.92 = $230,000
  target_offer = $250,000
  high_offer = 250,000 × 1.03 = $257,500

If asking_price < MAO (e.g., $200,000):
  low_offer = 200,000 × 0.95 = $190,000
  target_offer = min(250,000, 200,000) = $200,000
  high_offer = min(257,500, 200,000 × 1.02) = $204,000
```

### Timeline
- **High motivation:** 14-day close (seller wants out fast)
- **Medium/Low:** 21-day close (give room for negotiation)

### Cone Band Integration
- **Bands A/B:** Full follow-up cadence (4 touchpoints over 7 days)
- **Bands C/D:** Conservative cadence (2 light touchpoints, no escalation)

### Earnest Money
- **Canada:** CAD 500
- **USA:** USD 1,000

---

## Quick Example Workflow

```bash
# 1. Seed deals
curl -X POST "http://localhost:4000/core/deals/seed/generate?n=50&ca_ratio=0.5"

# 2. List deals
curl "http://localhost:4000/core/deals?limit=1" | jq '.items[0].id' → "uuid-123"

# 3. Get offer sheet
curl "http://localhost:4000/core/deals/uuid-123/offer_sheet" | jq '.'

# Output shows:
# - offer_guidance: 3-tier pricing
# - seller_angle: Customized by motivation
# - follow_up_cadence: 4 touchpoints (if A/B band)
# - disposition: Wholesale buyer checklist
# - restrictions: None (if A/B) or "no escalation" (if C/D)
```

---

## Files Created

**[backend/app/core_gov/deals/offer_sheet_service.py](backend/app/core_gov/deals/offer_sheet_service.py)** (120 lines)
- `_currency(country)` — Return CAD or USD
- `build_offer_sheet(deal)` — Main logic, returns complete offer sheet

**[backend/app/core_gov/deals/offer_sheet_router.py](backend/app/core_gov/deals/offer_sheet_router.py)** (13 lines)
- `GET /{deal_id}/offer_sheet` — Endpoint

---

## Integration

✅ Imported in core_router.py (line 30)  
✅ Included in core router (line 130)  
✅ Reads from: DB-4 scoring, Cone service  
✅ No audit event (advisory-only, no state change)  
✅ No new dependencies  

---

## Design Notes

### v1 Heuristics
- MAO calculation is from DB-4 scoring service (strategy-based formula)
- Offer ranges are simple multipliers: low=92%, target=100%, high=103%
- If asking < MAO, anchor closer to asking (don't overshoot)
- Terms are static: earnest 500/1000, inspection 7d, close 14/21d
- Follow-up cadence has 2 variants (A/B vs C/D)

### Future (v2+)
- Tune offer ranges per province/state (input from Knowledge Vault)
- Dynamic earnest money (% of offer)
- Adjustable inspection/close days (from underwriting packs)
- More objection scenarios + responses (from deal history)
- Buyer disposition profiles (buyer type → required docs)
- A/B test seller angles (psychology + data)

---

## Testing

```bash
# Test with high-motivation wholesale deal
DEAL_ID=$(curl -X POST "http://localhost:4000/core/deals" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "CA",
    "province_state": "ON",
    "city": "Toronto",
    "strategy": "wholesale",
    "arv": 500000,
    "asking_price": 350000,
    "est_repairs": 40000,
    "seller_motivation": "high",
    "stage": "new"
  }' | jq -r '.id')

# Get offer sheet
curl "http://localhost:4000/core/deals/$DEAL_ID/offer_sheet" | jq '.'

# Verify:
# - offer_guidance has 3 offer tiers
# - seller_angle is "Speed + certainty"
# - follow_up_cadence has 4 touchpoints
# - disposition.buyer_type = "cash/investor"
# - restrictions = [] (Cone A/B)
```

---

## Summary

**DB-8** provides intelligent offer guidance from a scored deal:

1. **Pricing:** 3-tier guidance (low/target/high) based on MAO
2. **Terms:** Earnest money, inspection days, close timeline
3. **Psychology:** Seller angle customized by motivation
4. **Objections:** 3-response playbook for common pushback
5. **Follow-up:** Cone-aware cadence (expansion vs stabilization)
6. **Disposition:** Checklist for wholesale buyer package
7. **Restrictions:** Band C/D override (no escalation)

All advisory — user approves final numbers and terms.

Ready for: Real deal offers, agent training, auto-dialing scripts, buyer coordination.
