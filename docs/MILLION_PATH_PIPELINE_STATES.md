# MILLION-PATH: Pipeline States & Stage Progression

**Status:** CANONICAL DESIGN  
**Scope:** Day-one through multi-zone scale  
**Last Updated:** 2026-04-13  

---

## EXECUTION LAYER PIPELINE

The system moves opportunities through defined stages. Each stage represents a clear progression in deal viability.

---

## LAUNCH BASELINE STAGES (Day 1)

These stages are sufficient for the first WeWeb build.

### Stage 1: INTAKE
**Status:** New or under initial review  
**Entry Point:** POST /execution/intake  
**What Happens Here:** 
- Raw opportunity text captured
- Initial parsing/classification
- Quick viability check (is this real real estate?)

**Owner:** Operator / Intake VA  
**Tasks:** (None - auto-generated system analysis)  
**Duration:** < 5 minutes  
**Exit Criteria:**
- Sufficient data to classify
- Move to PROCESSED

**Output:** Raw opportunity record with status="new"

---

### Stage 2: INTAKE_PROCESSED
**Status:** System has analyzed, awaiting decision  
**Entry Point:** POST /execution/intake/{intake_id}/process  
**What Happens Here:**
- Full ML classification (property type, market, strategy viability)
- Profit margin calculation
- Risk assessment
- Decision logic runs
- If blocked: blocked=true, blocker_reason = "why"
- If viable: blocked=false, next actions queued

**Owner:** System (operator views result)  
**Tasks Generated:**
- Verify property exists
- Contact seller
- Calculate spread
- Make go/no-go decision

**Duration:** 1-3 days (operator does the tasks)  
**Exit Criteria:**
- Operator manually approves ("looks good")
- System auto-escalates if margin < 5%
- Move to READY_FOR_CONTACT or ESCALATION_REQUIRED

**Output:** Full execution_case record with classification, tasks, next action

---

### Stage 3: READY_FOR_CONTACT
**Status:** Approved, now time to contact seller  
**Entry Point:** POST /execution/cases/{case_id}/advance  
**When:** Operator clicks "Approve & Proceed" after reviewing INTAKE_PROCESSED

**What Happens Here:**
- Case marked active (not blocked)
- Followup VA gets notified
- Contact workflow begins

**Owner:** Followup VA  
**Tasks Generated:**
- Call/email seller to confirm motivation
- Build rapport
- Initial information gathering

**Duration:** 2-7 days  
**Exit Criteria:**
- Seller responds (or doesn't)
- Seller engaged → CONTACTED
- Seller not responsive → DEAD
- Seller wants to list conventionally → PASS

**Output:** Updated case with contact_status, seller_notes

---

### Stage 4: CONTACTED
**Status:** Seller engaged, negotiating terms  
**Entry Point:** Automatic when followup logs contact, OR manual stage trigger  
**What Happens Here:**
- Initial seller negotiation begins
- Terms discussion (timeline, condition, price flexibility)
- Building partnership

**Owner:** Closer / Negotiations team  
**Tasks Generated:**
- Present offer framework
- Discuss timeline
- Understand seller constraints
- Get preliminary agreement on terms

**Duration:** 3-14 days  
**Exit Criteria:**
- Seller agrees to our terms → NEGOTIATING
- Seller wants too much → DEAD
- Seller prefers MLS → PASS
- Seller wants retail → PARTNERSHIP_OFFER

**Output:** Case with negotiation_status, preliminary_terms

---

### Stage 5: NEGOTIATING
**Status:** Terms being locked down  
**Entry Point:** When terms moving to contract stage  
**What Happens Here:**
- Fine-tuning offer
- Inspection contingency discussions
- Timeline finalization
- Purchase terms document being prepared

**Owner:** Closer / Legal  
**Tasks Generated:**
- Finalize offer documents
- Get inspection results
- Verify title/liens
- Prepare contract

**Duration:** 2-7 days  
**Exit Criteria:**
- All parties agree → UNDER_CONTRACT
- Inspection reveals deal-breaker → DEAD
- Seller backs out → DEAD

**Output:** Case with final_terms, inspection_results, title_status

---

### Stage 6: UNDER_CONTRACT
**Status:** Contract signed, deal committed  
**Entry Point:** When purchase agreement signed  
**What Happens Here:**
- Legally binding deal
- Inspection period active
- Funding coordination begins
- Closing preparation

**Owner:** Acquisitions / Title Company  
**Tasks Generated:**
- Order full inspection
- Title search
- Arrange financing
- Coordinate closing date

**Duration:** 5-30 days (inspection + underwriting)  
**Exit Criteria:**
- All contingencies clear → READY_TO_CLOSE
- Inspection issues → negotiate or withdraw
- Funding denied → DEAD

**Output:** Case with contract_date, closing_date, funding_status

---

### Stage 7: CLOSED
**Status:** Deal closed, ownership transferred  
**Entry Point:** When deed is recorded  
**What Happens Here:**
- Cash/asset now owned
- Disposition workflow begins
- Post-acquisition work starts (rehabilitation, direct sale, hold, partnership)

**Owner:** Operations / Dispo team  
**Tasks Generated:**
- Coordinate closing logistics
- Take ownership
- Arrange disposition (sell wholesale, retail, hold, partnership exit)

**Duration:** Ongoing per strategy  
**Exit Criteria:**
- For wholesale: buyer found and paid → DISPOSED
- For hold: moved to holdings portfolio → PORTFOLIO
- For partnership: partner transitioned → PARTNERSHIP_ACTIVE
- For development: rehab team assigned → REHAB_IN_PROGRESS

**Output:** Case marked closed with strategy_disposition, ownership_details

---

### Stage 8: DEAD
**Status:** Opportunity rejected  
**Entry Point:** Operator clicks "Pass", or system detects disqualifier, or seller unresponsive  
**When:**
- Margin too low after detailed analysis
- Seller not responsive after 2 weeks
- Property doesn't match description
- Inspection reveals major issue
- Seller wants retail only
- Better opportunity found

**Owner:** System or operator  
**Tasks Generated:** (None - deal archived)

**Duration:** End state (terminal)  
**Exit Criteria:** (None - this is final)

**Output:** Case with death_reason, death_timestamp, post_mortem_notes

---

## OPTIONAL ADVANCED STAGES (Year 2+)

These stages support advanced workflows but are NOT required for day-one.

### Stage 9: DISPO_READY (Optional - Post-Launch)
**Purpose:** Closed deals queued for disposition  
**Owner:** Dispo specialist  
**Tasks:** - Find buyer, - Negotiate buyer terms, - Close with buyer

### Stage 10: BUYER_MATCHING (Optional - Advanced)
**Purpose:** System finding ideal buyers from registry  
**Owner:** Dispo specialist + AI  
**Tasks:** - Rank buyer matches, - Contact buyers, - Coordinate buyer preview

### Stage 11: HOLD_REVIEW (Optional - Advanced)
**Purpose:** Monthly review of held properties  
**Owner:** Zone lead  
**Tasks:** - Market analysis, - Rental performance review, - Exit strategy evaluation

### Stage 12: PARTNERSHIP_REVIEW (Optional - Advanced)
**Purpose:** Partnership deals in progress  
**Owner:** Partner manager  
**Tasks:** - Partner coordination, - Performance tracking, - Distribution preparation

### Stage 13: LEGAL_REVIEW (Optional - Advanced)
**Purpose:** Complex deals requiring legal review  
**Owner:** Legal team  
**Tasks:** - Legal analysis, - Dispute resolution, - Compliance check

### Stage 14: FUNDING_READY (Optional - Advanced)
**Purpose:** Deal approved for capital deployment  
**Owner:** Capital team  
**Tasks:** - Capital allocated, - Funding disbursed, - Escrow management

---

## STAGE TRANSITION DIAGRAM

```
INTAKE
  ↓
INTAKE_PROCESSED (System classifies)
  ├→ DEAD (margin < 5% or system blocks)
  ├→ ESCALATION_REQUIRED (manual review needed)
  └→ READY_FOR_CONTACT (operator approves)
      ↓
    CONTACTED (Seller engages)
      ├→ DEAD (not interested)
      ├→ PASS (wants retail)
      └→ NEGOTIATING (moving to terms)
          ↓
        UNDER_CONTRACT (Purchase agreement signed)
          ├→ DEAD (inspection fails, funding denied)
          └→ READY_TO_CLOSE (contingencies cleared)
              ↓
            CLOSED (Deed recorded, ownership transferred)
              ├→ DISPOSED (Wholesaled off)
              ├→ PORTFOLIO (Held for income/appreciation)
              ├→ PARTNERSHIP_ACTIVE (Partnered with buyer)
              └→ REHAB_IN_PROGRESS (Development/flip)
```

---

## CURRENT STAGE JSON REPRESENTATION

```python
# Current live execution_cases table uses:
current_stage: str  # Enum-like: "intake", "intake_processed", "contacted", etc.
current_status: str  # Secondary status: "pending_review", "active", "on_hold", etc.
blocked: bool  # True if cannot proceed (margin too low, etc.)
next_action: str  # What operator should do next

# Future scale model will add:
pipeline_stage: str  # Formal enum from this list
stage_history: list[dict]  # [{stage, timestamp, actor, notes}, ...]
sla_deadline: timestamp  # When should move to next stage
```

---

## STAGE OWNERSHIP & RESPONSIBILITIES

| Stage | Primary Owner | Backup Owner | Key Decision | SLA |
|-------|--------------|--------------|--------------|-----|
| INTAKE | Intake VA | Operator | Is this real real estate? | 15 min |
| INTAKE_PROCESSED | System/Operator | Zone lead | Approve proceed or escalate? | 24 hrs |
| READY_FOR_CONTACT | Followup VA | Closer | Ready to contact? | Immediate |
| CONTACTED | Followup VA | Closer | Is seller engaged? | 48 hrs |
| NEGOTIATING | Closer | Zone lead | Can we agree on terms? | 7 days |
| UNDER_CONTRACT | Acquisitions | Legal | Are contingencies clear? | 14 days |
| CLOSED | Operations | Owner | Move to portfolio/dispo | 1 day |
| DEAD | System or operator | Zone lead | Archive and note reason | N/A |

---

## SCORING & AUTOMATION

### Auto-Progression Rules (Future)

**INTAKE → INTAKE_PROCESSED:** Automatic after 5 minutes (for system to analyze)

**INTAKE_PROCESSED → DEAD:** Automatic if margin < 5% AND no manual override

**INTAKE_PROCESSED → READY_FOR_CONTACT:** Automatic if margin > 15% (safe case)

**CONTACTED → NEGOTIATING:** Manual (operator observes seller engagement, decides)

**UNDER_CONTRACT → READY_TO_CLOSE:** Automatic if inspection_passing=true AND funding_approved=true

**ANY STAGE → DEAD:** Automatic if 14+ days no activity (auto-timeout)

---

## STAGE DATA REQUIREMENTS

### At INTAKE_PROCESSED, system must provide:
```json
{
  "classification": {
    "case_type": "real_estate|commercial|land",
    "strategy": "wholesale|hold|flip|partnership",
    "property_type": "sfh|multifamily|commercial"
  },
  "financial": {
    "purchase_price_est": 250000,
    "arv_est": 300000,
    "repair_est": 10000,
    "profit_margin": 40000
  },
  "risk": {
    "risk_level": "low|medium|high|critical",
    "blocker_reason": "if blocked"
  }
}
```

### At CONTACTED, operator must log:
```json
{
  "seller_response": "interested|not_interested|wants_retail|needs_time",
  "seller_motivation": "str",
  "suggested_timeline": "days",
  "initial_terms_signal": "flexible|fixed|no_discussion"
}
```

### At UNDER_CONTRACT, we must have:
```json
{
  "purchase_agreement": {
    "signed_date": "2026-04-15",
    "purchase_price": 250000,
    "closing_date": "2026-05-15",
    "contingencies": ["inspection", "title", "appraisal"]
  },
  "funding": {
    "total_needed": 250000,
    "source": "savings|loan|partner|other",
    "approved": true
  }
}
```

---

## DEAD END REASONS & TRACKING

| Reason | Stage Trigger | Resolution | Archive? |
|--------|---------------|-----------|----------|
| Margin too low | INTAKE_PROCESSED | System auto-blocks | YES |
| Not real real estate | INTAKE_PROCESSED | Manual reject | YES |
| Seller not responsive | CONTACTED | After 14 days | YES |
| Seller wants retail only | CONTACTED | Offer partnership? | YES |
| Inspection fails | UNDER_CONTRACT | Try repair credit? | NO - keep option |
| Funding denied | UNDER_CONTRACT | Alternative financing? | NO - keep option |
| Partner backed out | PARTNERSHIP_ACTIVE | Default to hold/dispo? | MAYBE |
| Title issues | UNDER_CONTRACT | Legal review needed | NO - escalate |

---

## WEWEB REPRESENTATION

The first WeWeb build must display stage as:

```
Current Stage: INTAKE_PROCESSED
Status: ⚠️  PENDING REVIEW
Progress: ████░░░░░░ 40%

[BLOCKED: Needs Manual Review]
Reason: Profit margin 2.0% below 5% threshold

Next: [APPROVE] [REQUEST CLARIFICATION] [PASS]
```

---

## MIGRATION SAFETY

**This stage model can be applied:**
- ✅ As documentation immediately
- ✅ As constants enum in code now
- ❌ As database migration only after WeWeb stabilizes

**Current live system uses:**
- `current_stage` (string)
- `current_status` (string)
- `blocked` (boolean)
- This will not change for day-one

**Future migration will:**
- Add `pipeline_stage` column (new, nullable)
- Migrate `current_stage` values to new enum
- Keep old columns for 2-week compatibility window
- Remove old columns in week 3 post-launch

---

## NEXT STEPS

1. ✅ Finalize this stage list
2. ✅ Create enum values in code
3. ⏳ Apply to first WeWeb build (display only)
4. ⏳ Test stage transitions manually
5. ⏳ Post-launch: add auto-progression rules

---

**Document Owner:** Execution Layer Team  
**Status:** CANONICAL - Ready for implementation  
**Last Tested:** 2026-04-13  
