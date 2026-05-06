# WeWeb Token Budget Manifest

**Purpose**: Manage token spending efficiently across 7 WeEB pages  
**Strategy**: One page per focused prompt (not all 7 at once)  
**Total Budget**: ~150K-200K tokens (rough estimate for all 7 pages)

---

## Page-by-Page Token Cost & Strategy

### PROMPT 1: Lead Submission Form (~8-12K tokens)
**Scope**: Single form page, POST to one endpoint, response display  
**What to Ask**: "Build Lead Submission form with these fields..."  
**Don't Ask**: Multiple pages, routing, navigation, styling everything  
**Stop Point**: After testing form submission works  
**Next**: "That works! Ready for prompt 2."

**Estimated Cost**: 
- Request: 2K
- Response: 6-8K  
- Follow-up fixes: 2-4K
- **Total**: 8-12K

---

### PROMPT 2: Leads List & Filter (~10-15K tokens)
**Scope**: Data table, pagination, optional filter  
**What to Ask**: "Build Lead List with table and filter..."  
**Don't Ask**: Add edit/delete buttons, bulk operations, export  
**Stop Point**: After table loads data and filter works  
**Next**: "Table works! Ready for prompt 3."

**Estimated Cost**:
- Request: 2K
- Response: 8-10K
- Follow-up fixes: 2-3K
- **Total**: 10-15K

---

### PROMPT 3: Lead Detail Page (~12-18K tokens)
**Scope**: Single record display, read-only fields, audit trail, buttons  
**What to Ask**: "Build Lead Detail page showing [specific fields]..."  
**Don't Ask**: Edit mode, inline updates, related records  
**Stop Point**: After detail loads and audit trail expands  
**Next**: "Detail page works! Ready for prompt 4."

**Estimated Cost**:
- Request: 2.5K
- Response: 10-13K
- Follow-up fixes: 2-4K
- **Total**: 12-18K

---

### PROMPT 4: Approval Queue (~12-16K tokens)
**Scope**: Data table, approve/deny modals, status updates  
**What to Ask**: "Build Approval Queue with modal dialogs for approve/deny..."  
**Don't Ask**: Bulk approvals, approval rules, reassignment  
**Stop Point**: After approve/deny modals work and status updates  
**Next**: "Queue works! Ready for prompt 5."

**Estimated Cost**:
- Request: 2.5K
- Response: 10-12K
- Follow-up fixes: 2-3K
- **Total**: 12-16K

---

### PROMPT 5: Draft Message Page (~10-14K tokens)
**Scope**: Lead selector, message type radio buttons, POST draft, display  
**What to Ask**: "Build Draft Message page with message type selector..."  
**Don't Ask**: Send functionality, template editor, revision history  
**Stop Point**: After draft generates and displays  
**Next**: "Draft works! Ready for prompt 6."

**Estimated Cost**:
- Request: 2K
- Response: 8-10K
- Follow-up fixes: 2-3K
- **Total**: 10-14K

---

### PROMPT 6: Reports Dashboard (~15-20K tokens)
**Scope**: Cards, 3-4 charts, summary table  
**What to Ask**: "Build Reports Dashboard with cards and charts using [APIs]..."  
**Don't Ask**: Drill-down details, date range selectors, export to PDF  
**Stop Point**: After charts display and update  
**Next**: "Charts work! Ready for prompt 7."

**Estimated Cost**:
- Request: 2.5K
- Response: 12-15K
- Follow-up fixes: 2-4K
- **Total**: 15-20K

---

### PROMPT 7: Navigation & Shell (~8-12K tokens)
**Scope**: Menu structure, routing, status indicator  
**What to Ask**: "Build navigation menu and routing for [pages]..."  
**Don't Ask**: User settings, theme switcher, advanced UI features  
**Stop Point**: After all pages route and menu works  
**Next**: "DONE! All 7 pages built."

**Estimated Cost**:
- Request: 2K
- Response: 6-8K
- Follow-up fixes: 2-3K
- **Total**: 8-12K

---

## Total Token Budget Summary

| Page | Low | High | Notes |
|------|-----|------|-------|
| 1. Form | 8K | 12K | Straightforward POST |
| 2. List | 10K | 15K | Table + filter |
| 3. Detail | 12K | 18K | Multiple sections |
| 4. Queue | 12K | 16K | Modals for actions |
| 5. Message | 10K | 14K | Draft generation |
| 6. Reports | 15K | 20K | Charts most expensive |
| 7. Nav | 8K | 12K | Routing & shell |
| **TOTAL** | **75K** | **107K** | **Conservative: 130-150K** |

**Rule of Thumb**: Add 20-30% buffer for follow-ups, bugs, refinements

---

## Token Management Rules

### ✅ SAVE TOKENS - DO THIS
- **One page per prompt** - don't ask for 2-3 pages
- **Copy exact requirements** - reduce back-and-forth
- **Test thoroughly before next prompt** - avoid "wait, also add X"
- **Use the connection pack** - pre-written prompts are cheaper
- **Report issues clearly** - don't describe, paste error messages
- **Stop rules** - block before building wrong thing

### ❌ WASTE TOKENS - AVOID THIS
- ❌ "Also add a report page, and calendar, and..."
- ❌ "Can you redesign this because I don't like the styling?"
- ❌ "What if we tried a different approach?"
- ❌ Vague requirements - "make it pretty"
- ❌ Back-and-forth: "almost right, tweak X"
- ❌ "Wait, I also need..."

---

## Prompt Template - Copy & Paste

When you're ready to build a page, use this template:

```
I'm building the [PAGE NAME] for a WeWeb app connected to a FastAPI backend.

Use these exact field names and APIs:
[Paste the PROMPT section from WEWEB_CONNECTION_PACK.md]

Build this page ONLY. Stop when it works.

Test with this sample data:
[Paste test data if applicable]

I will test and say "works!" or report errors.
Do not ask for clarification - use the requirements as-is.
```

---

## Page Sequence

**MUST BUILD IN THIS ORDER**:

1. ✓ **Lead Submission Form** - Create leads (input)
2. ✓ **Leads List** - See what was created (output)
3. ✓ **Lead Detail** - Inspect one lead (details)
4. ✓ **Approval Queue** - Review & approve (workflow)
5. ✓ **Draft Message** - Plan communication (optional)
6. ✓ **Reports Dashboard** - Track metrics (analytics)
7. ✓ **Navigation & Shell** - Connect pages (routing)

**Don't skip around.** Each page depends on previous ones working.

---

## Weekly Token Budget Proposal

If working May 6-14 (8 days):

```
May 6:  Pages 1-2 (Form + List)          ~20K tokens
May 8:  Pages 3-4 (Detail + Queue)        ~28K tokens
May 10: Pages 5-6 (Message + Reports)     ~34K tokens
May 12: Page 7 (Navigation) + Testing     ~15K tokens
May 14: Bug fixes & polish                ~10K tokens
---
TOTAL:                                     ~107K tokens
```

**This keeps within 150K token budget** with buffer for failures.

---

## If Token Budget Gets Tight

**Priority Order (build these first, cut the rest)**:

1. **MUST HAVE**: Form → List → Approval Queue (core workflow)
2. **SHOULD HAVE**: Lead Detail → Navigation
3. **NICE TO HAVE**: Draft Message → Reports

If over budget: Build core 3 pages first, reports last.

---

## Debugging Budget Savers

**If something doesn't work, before asking for help**:

1. Check [WEWEB_CONNECTION_PACK.md](WEWEB_CONNECTION_PACK.md) - is requirement clear?
2. Check [PHASE_3_COMPLETION_SUMMARY.md](PHASE_3_COMPLETION_SUMMARY.md) - does endpoint exist?
3. Paste **exact error message** - don't summarize
4. Paste **request body** - show what you sent
5. Paste **response** - show what you got

This costs 1-2K tokens vs 10-15K for vague troubleshooting.

---

## Sign-Off Checklist

Before "shipping" WeWeb Phase 2b:

- [ ] All 7 pages built
- [ ] All 7 pages pass testing checklist from connection pack
- [ ] Form submits and creates leads
- [ ] List displays and filters
- [ ] Detail shows full record
- [ ] Approval queue works (approve/deny tested)
- [ ] Draft generates correctly
- [ ] Reports display data
- [ ] Navigation routes between all pages
- [ ] No console errors
- [ ] Responsive on mobile
- [ ] Backend commit 908d481 still frozen

---

## Next Phase After WeWeb Complete

**DO NOT expand backend until:**
- ✅ All 7 WeWeb pages built and tested
- ✅ End-to-end workflow works (form → list → detail → approve)
- ✅ No bugs reported for 24 hours
- ✅ May 14 deadline or later

**Then decide: ship, fix bugs, or add features.**

---

**Prepared**: 2026-05-06  
**Backend Locked**: Commit 908d481  
**Frontend Budget**: 75-130K tokens  
**Timeline**: May 6-14, 2026  
**Status**: Ready for WeWeb build
