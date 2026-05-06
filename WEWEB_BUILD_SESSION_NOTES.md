# WEWEB BUILD SESSION NOTES

## Rule
**One page at a time. No exceptions.**

## Workflow (Per Page)
1. Copy prompt from WEWEB_QUICK_PROMPTS.md
2. Paste into Copilot
3. Wait for build
4. Test page
5. Save screenshots to WEWEB_SCREENSHOTS/
6. Log errors to WEWEB_ERROR_LOGS/ (if any)
7. Only then continue to next page

## Page Sequence
- Page 1: Lead Submission Form (May 6)
- Page 2: Lead List & Filter (May 7)
- Page 3: Lead Detail (May 8)
- Page 4: Approval Queue (May 9)
- Page 5: Draft Message (May 10)
- Page 6: Reports Dashboard (May 12)
- Page 7: Navigation Shell (May 13)

## DO NOT
- ❌ Redesign anything
- ❌ Improvise features
- ❌ Add extra workflows
- ❌ Change backend field names
- ❌ Request multiple pages in one prompt
- ❌ Ask for "improvements"
- ❌ Build anything not in the prompt

## If Blocked
1. Capture exact error message
2. Test the backend endpoint manually first
3. If backend is issue: stop and report
4. If frontend is issue: describe exactly what's wrong
5. Only fix the blocker
6. Then resume from where you left off

## Testing Notes
- Test with sample data from WEWEB_CONNECTION_PACK.md
- Verify API response matches expected fields
- Check database persistence (data survives refresh)
- Verify workflow (click → action → update)
- Screenshot successful state

## Session Log
```
Page 1: 
  Status: [NOT STARTED]
  Issues: None yet
  
Page 2:
  Status: [NOT STARTED]
  Issues: None yet
  
Page 3:
  Status: [NOT STARTED]
  Issues: None yet
  
Page 4:
  Status: [NOT STARTED]
  Issues: None yet
  
Page 5:
  Status: [NOT STARTED]
  Issues: None yet
  
Page 6:
  Status: [NOT STARTED]
  Issues: None yet
  
Page 7:
  Status: [NOT STARTED]
  Issues: None yet
```

## Update This Log
After each page, update status to: [IN PROGRESS] → [TESTING] → [COMPLETE] or [BLOCKED]

## Links
- Connection Pack: WEWEB_CONNECTION_PACK.md
- Quick Prompts: WEWEB_QUICK_PROMPTS.md
- Token Budget: WEWEB_TOKEN_BUDGET_MANIFEST.md
- Endpoint List: FINAL_ENDPOINT_INVENTORY.md
