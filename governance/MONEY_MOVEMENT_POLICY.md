# VALHALLA MONEY MOVEMENT POLICY

**Core Principle:** Automation may increase speed, never authority.

---

## INTERNAL ACCOUNTS

Internal transfers are automated only when ALL conditions are met:

### Approval Required
- Explicit approval object must exist
- Single-use (approval cannot be replayed)
- Time-limited (30 minutes default TTL)
- Cannot extend beyond TTL

### Whitelist Enforcement
- Only registered internal accounts can receive automated transfers
- External/third-party accounts require manual approval
- Whitelist is explicit and auditable

### Caps Enforced
- Per-transfer limits by account purpose
- Daily limits by account purpose
- Exceeding caps → automatic rejection
- Caps are conservative by default

### Kill Switch Always Available
- Global freeze: one command activates
- Stops ALL pending transfers instantly
- No exceptions, no delay
- Always available to operator

---

## THIRD PARTIES

Third-party payments are **NOT automated**:

### Advisory Only (Today)
- Heimdall can recommend payment instructions
- Operator executes manually via bank portal
- No automatic wiring

### Assisted Execution (Future)
- May add assisted payment workflows later
- Still requires explicit operator approval per transfer
- Never "set and forget"

### Human Gate Required
- Irreversible actions (bank transfers) require human decision
- No automation of final execution step
- Audit trail shows human approval

---

## SYSTEM LAWS

These are non-negotiable:

### No Credentials Stored
- Bank login credentials are never stored in system
- Never in environment variables, config files, or database
- Only external banking APIs with rate-limited tokens

### No Secrets Logged
- Approval IDs logged (safe)
- Account IDs logged (safe)
- Amounts logged (safe)
- Full account numbers NEVER logged
- Credentials NEVER logged

### No Money Moves Without Approval
- Every transfer requires explicit approval object
- Approval object is single-use and expiring
- Executor checks ALL conditions before execution

### Audit Everything
- Every approval creation logged
- Every execution attempt logged (success and failure)
- Kill switch activations logged
- Account registrations logged
- Caps exceeded logged

---

## ACCOUNT PURPOSES & DEFAULT CAPS

### OPERATING
- **Purpose:** Day-to-day operational expenses
- **Per Transfer:** $5,000
- **Daily:** $15,000
- **Use:** Automated for internal transfers

### RESERVE
- **Purpose:** Emergency/stability buffer
- **In per transfer:** $20,000
- **Out per transfer:** $2,000
- **Daily:** $5,000
- **Use:** Protected outflows; larger inflows allowed

### TAX
- **Purpose:** Tax payment account
- **Per Transfer:** $10,000
- **Daily:** $10,000
- **Rule:** Scheduled transfers only (not ad-hoc)

### TRUST
- **Purpose:** Trust/fiduciary account
- **Rule:** Manual-only (no automation)
- **Reason:** Legal complexity, high scrutiny

### DEAL_STAGING
- **Purpose:** Temporary holding for deal executions
- **Per Transfer:** $2,000
- **Daily:** $4,000
- **Use:** Short-lived, high-control

### CREDIT
- **Purpose:** Credit facility account
- **Rule:** Read-only (no outflows from system)
- **Reason:** Managed externally

---

## APPROVAL LIFECYCLE

**Creation:**
```
operator requests transfer
→ Heimdall provides approval object
→ Operator approves (verbal/written confirmation)
→ Approval object created with 30-min TTL
```

**Execution:**
```
approval_id is provided to executor
→ All checks run (caps, whitelist, expiry, kill switch)
→ If all pass: transfer executes, approval marked used
→ If any fail: RuntimeError raised, approval unchanged
```

**Expiry:**
```
30 minutes after creation
→ Approval cannot be used
→ Executor rejects with "Approval expired"
→ Operator must request new approval for retry
```

---

## FAILURE MODES & RESPONSES

| Scenario | Response | Operator Action |
|----------|----------|-----------------|
| Kill switch active | All transfers rejected | Activate kill switch, investigate |
| Approval expired | Rejects with error | Request new approval |
| Cap exceeded | Rejects with error | Adjust amount or request exception |
| Not whitelisted | Rejects with error | Add to whitelist via registry |
| Approval already used | Rejects with error | Request new approval |

---

## OPERATOR PROTECTION

**You are protected from:**
- Accidental double-execution (single-use approvals)
- Runaway transfers (caps prevent large moves)
- Slow-to-react externals (kill switch freezes everything)
- Credential compromise (no credentials stored)
- Audit gaps (everything logged)

**What you must do:**
- Review approval objects before confirming
- Use kill switch immediately if anything looks wrong
- Never store credentials in system
- Never bypass caps without documented override

---

## AUDIT TRAIL

Every money movement creates a record:

```
approval_created: {
  timestamp: UTC,
  approval_id: UUID,
  from_account: ID,
  to_account: ID,
  amount: decimal,
  ttl_minutes: int,
  expires_at: UTC
}

execution_attempted: {
  timestamp: UTC,
  approval_id: UUID,
  result: "success" | "error",
  error_reason: (if failed),
  amount_transferred: (if success)
}

kill_switch_event: {
  timestamp: UTC,
  action: "activated" | "deactivated",
  operator: (if logged),
  active_approvals_frozen: count
}
```

---

## PHASE 3 REQUIREMENTS MET

✅ Internal transfers are automated only  
✅ Whitelist enforced  
✅ Caps enforced by default  
✅ Kill switch always available  
✅ No credentials stored  
✅ Everything audited  
✅ Single-use approvals prevent replay  
✅ Time-limited approvals prevent stale reuse  

---

## NEXT STEPS (PHASE 4+)

When ready:
1. Add assisted execution for third-party payments
2. Integrate real banking API
3. Expand caps based on actual usage patterns
4. Add cap exception workflow (with Heimdall review)

For now: **Internal automation is safe and locked.**
