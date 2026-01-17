# Pack 81–85: Dual-God Audit Spine (Heimdall + Loki + Specialists)

## Overview

Packs **81 → 85** finish the **God Case spine** that sits behind your
decision system:

1. Heimdall makes primary recommendations.
2. Loki challenges, critiques, or confirms.
3. Human specialists (lawyer, accountant, underwriter, etc.) review the hard cases.
4. Every rescan, override, disagreement, and final decision is **counted, time-stamped, and snapshot-logged**.

This is the **“black box flight recorder”** for your God-tier decision layer:
if anything ever goes wrong, you can reconstruct exactly **who said what, when, and why**.

---

## Pack 81 – Loki Review Counters

**Goal:** Track how often Loki is:
- Overruling Heimdall
- Confirming Heimdall
- Flagging risk / uncertainty
- Being overridden by humans

These counters let Heimdall’s optimization core see **when Loki is right, when he overreacts, and when humans are saving the day.**

### What this pack adds

- DB fields (already in migrations) to support:
  - `loki_confirm_count`
  - `loki_disagree_count`
  - `loki_soft_flag_count` (⚠️ “be careful”)
  - `loki_hard_block_count` (⛔ “do NOT do this”)
- A simple **update routine** that increments these counters every time:
  - A God Case is created or updated
  - Loki changes his stance on a case
  - A final decision is logged

### Implementation notes (how it behaves)

1. **On every dual-god evaluation:**
   - Compare Heimdall verdict vs Loki verdict.
   - Classify outcome as:
     - `CONFIRM` – both green
     - `DISAGREE` – one green, one red
     - `CAUTION` – Loki set to “soft flag” / “extra review”
     - `BLOCK` – Loki set to “hard stop”

2. **Increment the right counters** on the God Case / arbitration row.
3. Expose Loki counter stats to:
   - Heimdall’s optimization core
   - Your God Case dashboard (later pack)
   - CI / monitoring (for “is Loki going crazy?” checks)

---

## Pack 82 – God Case Rescan Fields

**Goal:** Give your system **explicit “rescan intelligence”**:
fields that record *why* a case is being revisited and *what changed*.

### What this pack adds

New fields (as per migration 82):

- `rescan_reason` – high-level reason for rescan, e.g.:
  - `NEW_DATA`
  - `LEGAL_UPDATE`
  - `HUMAN_OVERRIDE`
  - `MODEL_DRIFT_CHECK`
  - `PERIODIC_HEALTH_CHECK`
- `rescan_trigger_source`
  - `HEIMDALL`
  - `LOKI`
  - `SPECIALIST`
  - `SCHEDULER`
  - `MANUAL`
- `rescan_iteration` – integer counter (0, 1, 2, …)
- `rescan_notes` – free-form notes (“lawyer found CRA bulletin X, Loki disagreed”)

### How it behaves

- Whenever a God Case is **reopened**:
  - Increment `rescan_iteration`.
  - Set `rescan_reason` and `rescan_trigger_source`.
  - Append to `rescan_notes` (or create new entry).

- Heimdall can later:
  - See which cases are being re-fought too often.
  - Flag patterns where **bad data feeds** or **reg changes** cause multiple rescans.
  - Auto-tighten rules for high-volatility patterns.

---

## Pack 83 – Specialist Review Sync

**Goal:** Tighten the bridge between **God layer** and **human experts**:
lawyer, accountant, underwriter, planner, etc.

This pack assumes your **Specialist / Sync** models already exist; it wires them directly into God Cases.

### What this pack adds

- A stable link between:
  - `god_case_id`
  - `specialist_session_id` (one or many)
- Status fields like:
  - `specialist_required` (bool)
  - `specialist_completed` (bool)
  - `specialist_outcome` (`CONFIRM`, `TWEAKED`, `REJECTED`)
  - `specialist_notes` (short text)
- Helper methods / service layer for:
  - **Attaching** a specialist review to a God Case
  - Marking review as complete
  - Pushing a short outcome summary back into the God Case

### Example flow

1. Heimdall & Loki strongly disagree on a BRRRR deal structure.
2. Loki’s counters increment; a **God Case** is opened.
3. `specialist_required = True` and a **Lawyer Review** is triggered.
4. Lawyer session ends with:
   - Outcome: “Use structure B, not structure A.”
5. Pack 83 sync layer:
   - Links the specialist session to the God Case.
   - Stores `specialist_outcome = TWEAKED`.
   - Summarizes key notes for Heimdall’s learning core.
6. Heimdall now “knows” that for this pattern:
   - Loki’s caution was justified.
   - Lawyer prefers structure B.
   - Future recommendations should nudge toward structure B.

---

## Pack 84 – Dual-God Snapshot Fields

**Goal:** For every critical decision, save a compact **snapshot** of what both gods saw and said — without storing massive blobs of raw logs.

This is your **“flight recorder frame”** for the pair:

- What Heimdall recommended
- What Loki argued
- What the humans did
- What the final outcome was

### What this pack adds

Snapshot fields (already created by migration 84):

- `heimdall_snapshot` – JSON:
  - key heuristics Heimdall used
  - recommended actions
  - internal confidence score bands (high/med/low)
- `loki_snapshot` – JSON:
  - primary objections
  - risk categories (legal / tax / cashflow / reputational)
  - Loki’s recommended alternative(s)
- `human_snapshot` – JSON:
  - specialist outcomes (if any)
  - your final decision
  - any explicit overrides / comments

### How it behaves

- Whenever a **God Case is closed** (final decision made):

  1. Heimdall dumps a compact summary of:
     - “Why I originally said YES/NO.”
  2. Loki logs:
     - “Why I agreed/disagreed and what I suggested instead.”
  3. Specialist sync (Pack 83) adds:
     - Any legal / accounting / underwriting notes.
  4. Save all of this into the `*_snapshot` fields.

From then on, **every case becomes a training example**:

- Heimdall can later mine “past life” to improve thresholds and heuristics.
- Loki can calibrate when he’s overfiring vs under-protecting.
- You can audit *exactly* what the system knew at the time.

---

## Pack 85 – God Case Rescan Workflow Logic

**Goal:** Turn the rescan fields (Pack 82) into **real workflows**:
who gets notified, what gets re-evaluated, and when the case can finally be closed.

### What this pack adds

1. A simple **state machine** for cases:
   - `OPEN`
   - `AWAITING_SPECIALIST`
   - `AWAITING_GOD_RESCAN`
   - `READY_FOR_FINAL_DECISION`
   - `CLOSED`
2. Workflow rules:
   - If `specialist_required = True` and `specialist_completed = False`:
     - Move to `AWAITING_SPECIALIST`
   - When specialist completes:
     - Move to `AWAITING_GOD_RESCAN`
   - When Heimdall/Loki rerun their evaluation:
     - Update counters + snapshots
     - Move to `READY_FOR_FINAL_DECISION`
   - When you sign off:
     - Move to `CLOSED`
3. Auto-rescan triggers:
   - If a **regulatory change** or **tax rule update** hits a class of deals:
     - Mark matching cases with `rescan_reason = LEGAL_UPDATE`
     - Increment `rescan_iteration`
     - Push them into `AWAITING_GOD_RESCAN`

### Example lifecycle

1. **Case 101**: First BRRRR in New Zone X
   - Heimdall: ✅
   - Loki: ⚠️ (legal risk)
   - State: `OPEN`
2. Pack 85 logic:
   - Flags `specialist_required = True`
   - State → `AWAITING_SPECIALIST`
3. Lawyer reviews and adjusts structure:
   - `specialist_completed = True`
   - `specialist_outcome = TWEAKED`
   - State → `AWAITING_GOD_RESCAN`
4. Heimdall & Loki rerun with new structure:
   - Heimdall: ✅ (higher safety)
   - Loki: ✅ (risks addressed)
   - Loki confirm / disagree counters updated
   - Snapshots saved
   - State → `READY_FOR_FINAL_DECISION`
5. You approve:
   - State → `CLOSED`
   - Case becomes a **golden training example** for future Zone X deals.

---

## Summary

Packs **81–85** complete the **Dual-God Audit Spine**:

1. **Pack 81 – Loki Review Counters**
   - Know when Loki is saving you vs slowing you down.

2. **Pack 82 – God Case Rescan Fields**
   - Every revisit has a reason, a source, and a count.

3. **Pack 83 – Specialist Review Sync**
   - Human experts plug cleanly into the God Case.

4. **Pack 84 – Dual-God Snapshot Fields**
   - Tiny “flight recorder frames” for Heimdall, Loki, and specialists.

5. **Pack 85 – God Case Rescan Workflow Logic**
   - Cases move through clear states until truly done.

Once this spine is in place, Heimdall’s optimization core gets a **clear, structured history** of:

- When he was right or wrong,
- When Loki was right or wrong,
- When humans stepped in,
- And what the final, safest structure was.

From here, the next packs can safely focus on **Eternal Optimization** and **Global